import React, { useState, useEffect } from 'react';
import { PlusCircle, Loader2, Trash2, RefreshCw } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import YoutubeSearch from './youtube-search';

const API_BASE_URL = 'http://localhost:5017/youtube';

const YoutubeChannelManager = () => {
  const [channelUrl, setChannelUrl] = useState('');
  const [channels, setChannels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [indexingStatus, setIndexingStatus] = useState('idle');
  const [activeTab, setActiveTab] = useState('search');

  useEffect(() => {
    fetchChannels();
  }, []);

  const addChannel = async () => {
    if (!channelUrl.trim()) return;
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/channels`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: channelUrl }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to add channel');
      }

      await fetchChannels();
      setChannelUrl('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchChannels = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/channels`);
      if (!response.ok) throw new Error('Failed to fetch channels');
      const data = await response.json();
      
      setChannels(data.channels || []);
    } catch (err) {
      setError(err.message);
    }
  };

  const removeChannel = async (channelId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/channels/${channelId}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to remove channel');
      }
      
      await fetchChannels();
    } catch (err) {
      setError(err.message);
    }
  };

  const reindexChannels = async () => {
    setIndexingStatus('indexing');
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/reindex`, {
        method: 'POST',
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to reindex channels');
      }
      
      setIndexingStatus('completed');
      await fetchChannels();
      setTimeout(() => setIndexingStatus('idle'), 3000);
    } catch (err) {
      setError(err.message);
      setIndexingStatus('error');
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch (e) {
      return dateString;
    }
  };

  return (
    <div>
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2 max-w-md mx-auto bg-neutral-800/50 mb-6">
          <TabsTrigger 
            value="search" 
            className="data-[state=active]:bg-red-600 data-[state=active]:text-white"
          >
            Search
          </TabsTrigger>
          <TabsTrigger 
            value="manage" 
            className="data-[state=active]:bg-red-600 data-[state=active]:text-white"
          >
            Manage Channels
          </TabsTrigger>
        </TabsList>

        <TabsContent value="manage">
          <Card className="bg-neutral-800/50 border-neutral-700 mb-6 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-xl text-white">Add YouTube Channel</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4 mb-4">
                <Input
                  type="text"
                  placeholder="Enter YouTube channel URL"
                  value={channelUrl}
                  onChange={(e) => setChannelUrl(e.target.value)}
                  className="bg-neutral-900 border-neutral-700 text-white placeholder-gray-400 focus:border-red-500 focus:ring-red-500"
                />
                <Button
                  onClick={addChannel}
                  disabled={loading || !channelUrl.trim()}
                  className="bg-red-600 hover:bg-red-700 text-white"
                >
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <PlusCircle className="h-4 w-4" />
                  )}
                  <span className="ml-2">Add</span>
                </Button>
              </div>

              <Button
                onClick={reindexChannels}
                disabled={indexingStatus === 'indexing' || channels.length === 0}
                className="w-full bg-neutral-700 hover:bg-neutral-600 text-white"
              >
                {indexingStatus === 'indexing' ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Indexing...
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Reindex All Channels
                  </>
                )}
              </Button>

              {error && (
                <Alert variant="destructive" className="mt-4 bg-red-900/20 border-red-900">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          <div className="space-y-4">
            {channels.map((channel) => (
              <Card key={channel.id || channel.video_id} className="bg-neutral-800/50 border-neutral-700 backdrop-blur-sm">
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-lg text-white">{channel.title}</CardTitle>
                    <p className="text-sm text-gray-400">
                      {channel.transcripts_count || channel.videoCount || 0} videos indexed • 
                      Last updated: {formatDate(channel.indexed_at || channel.lastUpdated)}
                    </p>
                  </div>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => removeChannel(channel.id || channel.video_id)}
                    className="bg-red-600 hover:bg-red-700"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </CardHeader>
              </Card>
            ))}

            {channels.length === 0 && (
              <div className="text-center text-gray-400 py-8 bg-neutral-800/50 rounded-lg border border-neutral-700 backdrop-blur-sm">
                No channels added yet
              </div>
            )}
          </div>
        </TabsContent>

        <TabsContent value="search">
          <YoutubeSearch />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default YoutubeChannelManager;
