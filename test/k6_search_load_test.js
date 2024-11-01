import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 1000,
  duration: '30s',
};

export default function () {
  const searchTerms = [
    'redis',
    'database',
    'cache',
    'performance',
    'scaling',
    'NoSQL',
    'in-memory',
    'key-value',
    'data structure',
    'persistence',
  ];

  const searchTerm = searchTerms[Math.floor(Math.random() * searchTerms.length)];

  const searchModes = ['tfidf', 'fulltext'];
  const searchMode = searchModes[Math.floor(Math.random() * searchModes.length)];

  // Make the search request
  const response = http.get(`http://localhost:5017/search?q=${encodeURIComponent(searchTerm)}&mode=${searchMode}`);

  check(response, {
    'is status 200': (r) => r.status === 200,
    'response body is not empty': (r) => r.body.length > 0,
  });

  console.log(`Search for "${searchTerm}" using ${searchMode} mode took ${response.timings.duration} ms`);

  sleep(Math.random() * 3);
}
