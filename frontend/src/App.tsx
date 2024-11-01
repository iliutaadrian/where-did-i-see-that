import './App.css'
import YoutubeChannelManager from './components/youtube-channel-manager'

function App() {
  return (
    <div className="min-h-screen w-full m-0 p-0">
      <div className="mx-auto max-w-4xl">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold mb-4">
            <span className="text-white">Where Did I</span>
            <span className="text-red-600"> See </span>
            <span className="text-white">That?</span>
          </h1>
          <p className="text-gray-400 mb-6">Your Personal YouTube Content Search Engine</p>
        </div>
        <YoutubeChannelManager />
      </div>
    </div>
  )
}

export default App
