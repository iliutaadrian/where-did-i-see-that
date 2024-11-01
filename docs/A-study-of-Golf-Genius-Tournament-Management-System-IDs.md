# Synopsis

This short study attempts to understand how ids are used in the Golf Genius Tournament Management System project.
This was prompted by the 2023 outage in an attempt to better understand what happened and how we can prevent/act in the future.

# What caused the outage?

The outage was caused by the fact that our ID encoding started generating IDs bigger than the maximum values that can be stored in the postgres BIGINT type resulting in negative ids due to overflow.

# How the ID encoding/decoding works

The ID `encode` and `decode` methods can be found in the `Sharding::IdManagement` defined at `app/lib/sharding/id_management.rb`.

For encoding we do the next steps in sequential order:
  - First we get the current time multiply it by a thousand and subtract our epoch from it.
  - Then we left shift by 25 bits the above time
  - We left shift by 9 bits the shard id and OR the bits with the previous result
  - We divide the old_id by 512 and take the module of that operation OR the bits with the previous results and return the result as the final encoded id

For decoding we do the above steps in reverse.

> A key takeaway from the above algorithm is that the timestamp has the biggest impact on how big the number representing the ID will be.

# When did it start?

In our implementation the `old_id` doesn't affect the size too much as we divide it by `512` and keep the remainder so a value of `511` (or multiple thereof) will increase the number the most.
The shard number also plays a role in the size of the number so `103` the largest id of a shard we currently have will ad the most to the value.
Then a custom encoding implementation was created that acts the same as the original it just takes an exact time for the encoding instead of `Time.now`.

```
 MAX_PSQL_BIG_INT = 9223372036854775807

 MAX_PSQL_BIG_INT > REPRODUCIBLE_ID_ENCODING.encode(511, 103, "2023-01-28 05:51:46 +0200".to_time)
 => true
 MAX_PSQL_BIG_INT > REPRODUCIBLE_ID_ENCODING.encode(511, 103, "2023-01-28 05:51:47 +0200".to_time)
 => false
```

> We can see from the above that the first overflow was bound to occur on `2023-01-28 05:51:47 +2UTC`

# How efficient is the current system

We use the following code to get the amount of ids we store in the db(only the primary key no foreign keys).
*There is an error in the below code that counts things found in shard 1 like user ids for the for every shard. This result in to many ids but I did not fix it to highlight the following conclusions.*

```ruby
def check_how_many_ids_there_are
  Rails.application.eager_load!
  model_names = ActiveRecord::Base.descendants.map(&:name)

  id_count = 0

  LogicalShard.order(:physical_shard).map do |ls|
    LogicalShard.switch_tenant!(ls.id)
    model_names.each do |model_name|
      begin
        id_count += (model_name&.constantize&.count(:all).to_i) if model_name&.constantize&.primary_key == 'id'
      rescue StandardError
        nil
      end
    end
  end

  id_count
end
```

The above code returns, as of 2023-02-07, `32_022_197_342`(~32 billion ids)

`CURRENT_NUMBER_OF_IDS = 32022197342` # (On the upper size due to the wrong calculation)

`MAX_PSQL_BIG_INT = 9223372036854775807` # This is aprox. 9 quintillion

Lets format the numbers to get a better picture of the difference between them:
- `9_223_370_916_077_868_837`
- `           32_022_197_342`
- `   92_233_720_368_547_758` (~1% of the maximum possible value)

The number of ids we have stored represent (3.47185359 × 10-7)% (~0.0000003%) of the maximum storage space available.

> We reached the big int limit from 2014 to 2023 by wasting over `99.9999997%` of the available space!!

Between every passing second we waste *over 33 billion positions* :

`REPRODUCIBLE_ID_ENCODING.encode(511, 103, "2023-01-28 05:51:47 +0200".to_time) - REPRODUCIBLE_ID_ENCODING.encode(511, 103, "2023-01-28 05:51:46 +0200".to_time)` => `33554432000`

`REPRODUCIBLE_ID_ENCODING.encode(511, 103, "2023-01-28 05:51:48 +0200".to_time) - REPRODUCIBLE_ID_ENCODING.encode(511, 103, "2023-01-28 05:51:47 +0200".to_time)` => `33554432000`


> Even with our current implementation it's clear that something must be done regarding this algorithm as it it extremely wasteful.


# The current Implemented solution

The way the current fix was implemented is by switching from `bigint` as the id type for primary and foreign keys to `numeric(22, 0)`.
This type acts similar to `varchar` in the db and the `(22, 0)` part means it can hold a number with 22 numbers for the integral part and 0 numbers for the fractal part.
This gives us a range limit between `0 and 9999999999999999999999`.

`ActiveRecord` interprets the new column type like this:
```ruby
#<ActiveRecord::ConnectionAdapters::PostgreSQLColumn:0x00007fc2dbbc0098
    @collation=nil,
    @comment=nil,
    @default=nil,
    @default_function="MODEL_TABLE_NAME_id_seq1()",
    @max_identifier_length=63,
    @name="id",
    @null=false,
    @sql_type_metadata=
        #<ActiveRecord::ConnectionAdapters::SqlTypeMetadata:0x00007fc2dbbc0778
            @limit=nil,
            @precision=22,
            @scale=nil,
            @sql_type="numeric(22,0)",
            @type=:decimal>,
```

IDs in this format can't overflow but instead psql returns an error of going above the limit.

```
:030 > Gpu::Scorecard.find(9999999999999999999999).update_columns({id: (CURRENT_MAX + 1)})
Gpu::Scorecard Load (1.9ms)  SELECT  "c103"."gpu_scorecards".* FROM "c103"."gpu_scorecards" WHERE "c103"."gpu_scorecards"."id" = 9999999999999999999999 LIMIT 1
↳ (irb):30:in `irb_binding'
SQL (1.9ms)  UPDATE "c103"."gpu_scorecards" SET "id" = 10000000000000000000000 WHERE "c103"."gpu_scorecards"."id" = 9999999999999999999999
↳ (irb):30:in `irb_binding'
Traceback (most recent call last):
      5: from (irb):30
      4: from config/initializers/postgresql.rb:80:in `exec_no_cache'
      3: from config/initializers/postgresql.rb:81:in `block in exec_no_cache'
      2: from config/initializers/postgresql.rb:82:in `block (2 levels) in exec_no_cache'
      1: from config/initializers/postgresql.rb:82:in `async_exec'
ActiveRecord::RangeError (PG::NumericValueOutOfRange: ERROR:  numeric field overflow)
DETAIL:  A field with precision 22, scale 0 must round to an absolute value less than 10^22.
: UPDATE "c103"."gpu_scorecards" SET "id" = 10000000000000000000000 WHERE "c103"."gpu_scorecards"."id" = 9999999999999999999999
```

## SQL Representation of numeric

Some additional data about the pslq numeric type.

From the [manual](https://www.postgresql.org/docs/current/datatype-numeric.html#DATATYPE-NUMERIC-DECIMAL):

Numeric values are physically stored without any extra leading or trailing zeroes.
Thus, the declared precision and scale of a column are maximums, not fixed allocations.
(In this sense the numeric type is more akin to varchar(n) than to char(n).)
The actual storage requirement is two bytes for each group of four decimal digits, plus three to eight bytes overhead.

```
pg_column_size ( "any" ) → integer
    Shows the number of bytes used to store any individual data value. If applied directly to a table column value, this reflects any compression that was done.
```

The result of the [pg_total_relation_size](https://www.postgresql.org/docs/current/functions-admin.html#FUNCTIONS-ADMIN-DBOBJECT) function includes indexes.
The correct column size for each of the values you are inserting is:

```
select pg_column_size(a)
from (values
    (9999999999999999999999::numeric(22,0))
) s(a)
;
```

```
 pg_column_size 
----------------
             18
(1 row)
```

## Solving the negative IDs

The negative IDs that were still in the database were recovered by implementing the `Migrate.fix_negative_ids(shard_id: nil, update: false, json_suffix: '')` method in `app/lib/migrate.rb`.
This was ran using jobs from the console (declared here: `app/lib/resque_libraries/resque_negative_ids.rb`) per shard in batches of *20* at a time as to not overload the server.
JSON files where created before, during and after updates to keep track of the data that was being modified.

The way the method for fixing the id works if by loading all the models and checking for columns of the type `['numeric(22,0)', 'bigint']` that had values below a certain ` _threshold = -9000000000000000000`. We needed to check for ids using a threshold because there are other columns of that type that can hold negative numbers, but none as low as the threshold making this a sure way that anything less was an overflown id. We also could not have relied on the column name as not every column has `_id` in its name.

After finding the negative ids all we do is get the difference between the id and the smallest possible value of big int in psql `diff = _min_big_int - negative_id` and then add the difference + 1 to the max possible value of a big int `fixed_id = (_MAX_BIG_INT - diff) + 1` (NOTE: `diff` is negative so - diff adds to `_MAX_BIG_INT`) which is the original encoded value that can now be stored in the now larger column type.

## Problems caused by the fix

### Increased database size
  The went up as result of switching from `bigint 8bytes` too `numberic(22, 0) 18 bytes`.
  If the number of ids currently is `32022197342` then this increased the dbs size by: (32022197342 * 18 bytes) - (32022197342 * 8 bytes) ~= `320.22Gb`

  > This does not include the high amount of foreign keys we have stored which will gratly increase the above number

  Here we had to increase the available space for the database.

### Mobile id errors
  This mostly affected our android apps as the ids were stored in the same integer format which was affected by the overflow.
  Changes were made to hold all ids as strings as there is no default datatype in java that can hold higher values.

### Raw queries having `.0` appended to the ID
  Due to the new numeric format some queries had `.0` appended to the id which we used in some url causing the next problem.
  Queries had to be changed adding the psql function `TO_CHAR()` where the problem occurred.

### Some URL links having `.0` appended to the ID
  This mainly happened due to the previous error caused by raw queries.
  It was isolated and solved with the previous fix as rails seems to be aware that a numeric type with 0 scale needs to be treated as an integer.

# Possible alternative fixes

It's important to analyse the possible alternative fixes to better understand the effects of the situation and to see if we can improve anything in the future for this type of scenarios.

## Reformatting Ids to better utilise the space by changing the timestamp of each encoded id

This would have involved optimising the encoding algorithm to better utilise the available space and then set up multiple jobs to recalculate all the ids.

This would have avoided the problems caused by the current fix.

Drawbacks to this would have been the required time to optimise the algorithm and the time required to recalculate all ids.
This would also have messed up all our caching mechanisms and indexes would have most likely needed to be recalculated.

## Switching to Unsigned integer types

This would have potentially been a better solution [https://github.com/petere/pguint](https://github.com/petere/pguint) as installing this extension would have meant that all we needed to do was change the column types and fix the negative ids, avoiding all the problems caused by the current fix.

This would have doubled our max upper limit giving us enough time to come up with a replacement.

Not sure on the drawbacks here as I don't know how difficult it would have been to setup the extension.

# Possible future causes

## Reaching the limit again

Since in the current implementation of id encoding the timestamp has the biggest effect on how large the IDs are
we can check when the next limit will be reached by adding an offset in years to `Time.now` in the `Sharding::IdManagement.encode(old_id, shard_id)` method.

```
Time.now => 2023-02-08

Sharding::IdManagement.encode(987654321, 28) => 9255195101771086001 # Ok - With an offset of 0 years
Sharding::IdManagement.encode(987654321, 28) => 19845618181628508337 # Ok - With an offset of 10 years
Sharding::IdManagement.encode(987654321, 28) => 115142030552987613361 # Ok - With an offset of 100 years
Sharding::IdManagement.encode(987654321, 28) => 1068129345875071744177 # Ok - With an offset of 1000 years
Sharding::IdManagement.encode(987654321, 28) => 9539134146062927804593 # Ok - With an offset of 9000 years
Sharding::IdManagement.encode(987654321, 28) => 9999746518704956913841 # Ok - With an offset of 9435 years
Sharding::IdManagement.encode(987654321, 28) => 10000804691542622091441 # OVERFLOWS - With an offset of 9436 years
```

It's pretty safe to say that we won't reach this limit any time soon but due to the inefficient system of storing the ids this will result in a huge amount of wasted space.

## EPOCH expiration

This event will occur on `03:14:07 UTC on 19 January 2038` when the signed 32-bit integer that holds the date will overflow and give the date of `20:45:52 UTC on 13 December 1901`.
This will mess with the sequential calculation of our IDs.


This is the most likely cause of ID failure in the future for our system if not treater "properly".
At the time of writing there is no actual solution in place of how this will be handled.
Most likely a committee will be charged to come up with a new standard, most likely something non-intrusive like using an unsigned integer to prolong the date, switching to 64 bit representation or changing the way the date is calculated to take negative number of seconds into account.
There is a high chance that changes to this system will not involve any code changes on our part(unless they change the fact that the date is the number of seconds since EPOCH) but we will most likely need to apply patches to our tools(eg. the database).

# Preventive measures

- TBD: An alert will be implemented to send a notification when the ids reach 75% of maximum to give enough time to implement a fix.

# Takeaway

We are starting to reach a point where the data we store is large enough that seemingly small inefficiencies can very quickly spiral out of control and lead to unexpected/undesired results.
Going forward there needs to be a bigger emphasis on the efficiency of the code written as well of the efficiency of how we store the data.

We need to double check if we need to add new fields, or if we can get our required data from existing fields.

We need to check if we can use a smaller datatype to represent our data.
An example that comes to mind is the `score` field from the `Score` model. # 3981027412
  We use `integer` to store the score which is `4 bytes` and can hold values between `-2147483648 to +2147483647` which is overkill for scores as they don't even come close to this value.
  As of `2023-02-08` there are aprox. `3981027412` scores in the db. This means that to hold the score value we use 3981027412 * 4 bytes = ~15.92Gb
  If we use `smallint` to store the score which is `2 bytes` and can hold values between `-32768 to +32767` we would use 3981027412 * 2 bytes = ~7.96Gb

> Code clarity should never be sacrificed for data optimisation!

Any new tables(columns) added in the future should have in the respective PRs some study cases.
Recommendation for the study cases:
  - How many bytes are needed to store the new data.
  - A projection of how much this will increase the DB size (eg. if adding a new column to an existing table check how many record we have an multiply by the byte size of the new column)
