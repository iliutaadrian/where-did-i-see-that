"use client";
import React, { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Alert, AlertDescription } from './components/ui/alert';

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

      const response = await fetch(`/search?${params}`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Search failed');
      }

      setResults(data.search_results || []);
    } catch (err) {
      setError(err.message);
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
    <div className="min-h-screen bg-[#0f0f0f] text-white">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold mb-4">
            <span className="text-white">You</span>
            <span className="text-[#ff0000]">Tube</span>
            <span className="text-white"> Search</span>
          </h1>
          <p className="text-gray-400 mb-6">Search using BM25 and OpenAI embeddings</p>
        </div>

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
                bg-[#121212] 
                border-[#303030]
                hover:border-[#3ea6ff]
                focus:border-[#3ea6ff]
                focus:ring-1 
                focus:ring-[#3ea6ff]
                text-white
                placeholder-gray-400
                transition-all
                ${isFocused ? 'border-[#3ea6ff] ring-1 ring-[#3ea6ff]' : ''}
              `}
            />
          </div>
          <Button 
            onClick={handleSearch}
            disabled={loading || !query.trim()}
            className={`
              w-16 h-10
              rounded-r-full rounded-l-none
              bg-[#222222]
              hover:bg-[#303030]
              border border-l-0
              border-[#303030]
              ${isFocused ? 'border-[#3ea6ff]' : ''}
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
          <TabsList className="grid grid-cols-3 w-full max-w-md mx-auto bg-[#222222]">
            {Object.entries({
              hybrid: 'Hybrid Search',
              bm25: 'BM25',
              openai: 'OpenAI'
            }).map(([value, label]) => (
              <TabsTrigger
                key={value}
                value={value}
                className="data-[state=active]:bg-[#303030] data-[state=active]:text-[#3ea6ff]"
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
            <Card key={index} className="bg-[#222222] border-[#303030]">
              <CardHeader>
                <CardTitle 
                  className="text-lg text-[#3ea6ff]"
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
