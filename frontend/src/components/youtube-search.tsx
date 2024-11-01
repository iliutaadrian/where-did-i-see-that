"use client";
import React, { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';

const YoutubeSearch = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeMethod, setActiveMethod] = useState('hybrid');
  const [isFocused, setIsFocused] = useState(false);

  const searchMethods = {
    hybrid: {
      aggregationMethod: 'linear',
      syntacticMethods: ['bm25'],
      semanticMethods: ['openai']
    },
    bm25: {
      aggregationMethod: 'single',
      syntacticMethods: ['bm25'],
      semanticMethods: []
    },
    openai: {
      aggregationMethod: 'single',
      syntacticMethods: [],
      semanticMethods: ['openai']
    }
  };

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError('');

    try {
      const params = new URLSearchParams({
        q: query,
        aggregationMethod: searchMethods[activeMethod].aggregationMethod,
        syntacticMethods: JSON.stringify(searchMethods[activeMethod].syntacticMethods),
        semanticMethods: JSON.stringify(searchMethods[activeMethod].semanticMethods),
        options: JSON.stringify(['caching'])
      });

      const response = await fetch(`http://localhost:5017/search?${params}`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Search failed');
      }

      const data = await response.json();
      setResults(data.search_results || []);
    } catch (err) {
      console.error('Search error:', err);
      setError(err instanceof Error ? err.message : 'Search failed');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="min-h-screen text-white">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="flex gap-0 mb-6 max-w-2xl mx-auto">
          <div className={`flex-1 relative ${isFocused ? 'z-10' : ''}`}>
            <Input
              type="text"
              placeholder="Search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              className={`
                rounded-l-full rounded-r-none
                h-10 px-4 py-2
                bg-neutral-900
                border-neutral-700
                hover:border-blue-400
                focus:border-blue-400
                focus:ring-1 
                focus:ring-blue-400
                text-white
                placeholder-gray-400
                transition-all
                ${isFocused ? 'border-blue-400 ring-1 ring-blue-400' : ''}
              `}
            />
          </div>
          <Button
            onClick={handleSearch}
            disabled={loading || !query.trim()}
            className={`
              w-16 h-10
              rounded-r-full rounded-l-none
              bg-neutral-800
              hover:bg-neutral-700
              border border-l-0
              border-neutral-700
              ${isFocused ? 'border-blue-400' : ''}
              transition-all
            `}
          >
            {loading ? (
              <Loader2 className="h-5 w-5 animate-spin text-white" />
            ) : (
              <Search className="h-5 w-5 text-white" />
            )}
          </Button>
        </div>

        <Tabs
          value={activeMethod}
          onValueChange={setActiveMethod}
          className="mb-6"
        >
          <TabsList className="grid grid-cols-3 w-full max-w-md mx-auto bg-neutral-800">
            {Object.entries({
              hybrid: 'Hybrid Search',
              bm25: 'BM25',
              openai: 'OpenAI'
            }).map(([value, label]) => (
              <TabsTrigger
                key={value}
                value={value}
                className="data-[state=active]:bg-neutral-700 data-[state=active]:text-blue-400"
              >
                {label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>

        {error && (
          <Alert variant="destructive" className="mb-6 bg-red-900/20 border-red-900">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="space-y-4">
          {results.map((result, index) => (
            <Card key={index} className="bg-neutral-800 border-neutral-700">
              <CardHeader>
                <CardTitle
                  className="text-lg text-blue-400"
                  dangerouslySetInnerHTML={{ __html: result.highlighted_name }}
                />
              </CardHeader>
              <CardContent>
                <div
                  className="text-gray-300"
                  dangerouslySetInnerHTML={{ __html: result.content_snippet }}
                />
                <div className="mt-2 text-sm text-gray-400">
                  Relevance Score: {Math.round(result.relevance_score)}%
                </div>
              </CardContent>
            </Card>
          ))}

          {!loading && results.length === 0 && !error && query && (
            <div className="text-center text-gray-400 py-8">
              No results found for "{query}"
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default YoutubeSearch;
