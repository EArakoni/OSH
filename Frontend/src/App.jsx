import React, { useState, useEffect } from 'react';
import {
  BookOpen, Home, LogOut, Lock, Menu, X,
  Search, User, Unlock
} from 'lucide-react';

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [posts, setPosts] = useState([]);
  const [selectedPost, setSelectedPost] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const auth0Domain = 'dev-gsykrp7lbzxn8prq.us.auth0.com';
  const auth0ClientId = 'rMibqVnfRKY7kSlDeFVNZWdGLRYtXltH';
  const redirectUri = window.location.origin;
  const API_URL = 'http://localhost:5000';

  useEffect(() => {
    fetchThreads();
    checkAuth();
  }, []);

  const fetchThreads = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/threads?limit=50&sort=active`);

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }

      const data = await response.json();

      const normalized = Array.isArray(data.threads)
        ? data.threads.map(thread => ({
          id: thread.id,
          title: thread.subject || 'Untitled Patch',
          author: `${thread.participant_count} participants`,
          date: thread.last_post?.split('T')[0] || 'Unknown Date',
          excerpt: thread.tldr || 'No summary available.',
          tags: thread.tags || [],
          subsystems: thread.subsystems || [],
          simplified: thread.tldr || '',
          content: thread.tldr || '',
          emailCount: thread.email_count || 0
        }))
        : [];

      setPosts(normalized);
    } catch (err) {
      console.error('Error fetching threads:', err);
      setError(`Failed to load threads: ${err.message}. Is the backend running on ${API_URL}?`);
    } finally {
      setLoading(false);
    }
  };

  const checkAuth = () => {
    const hash = window.location.hash;
    if (hash.includes('access_token')) {
      const token = hash.split('access_token=')[1]?.split('&')[0];
      if (token) {
        setUser({
          name: 'Developer',
          email: 'dev@example.com',
          picture: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Developer'
        });
        setIsAuthenticated(true);
        window.history.replaceState({}, document.title, window.location.pathname);
      }
    }
  };

  const login = () => {
    const authUrl = `https://${auth0Domain}/authorize?response_type=token&client_id=${auth0ClientId}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=openid profile email`;
    window.location.href = authUrl;
  };

  const logout = () => {
    setIsAuthenticated(false);
    setUser(null);
    const logoutUrl = `https://${auth0Domain}/v2/logout?client_id=${auth0ClientId}&returnTo=${encodeURIComponent(redirectUri)}`;
    window.location.href = logoutUrl;
  };

  const filteredPosts = posts.filter(post =>
    post?.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    post?.tags?.some(tag => tag?.toLowerCase().includes(searchTerm.toLowerCase())) ||
    post?.subsystems?.some(sub => sub?.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <header className="bg-black/30 backdrop-blur-md border-b border-purple-500/20 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
              <BookOpen className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-white">
              KernelPatch<span className="text-purple-400">Digest</span>
            </h1>
          </div>
          <nav className="hidden md:flex items-center space-x-6">
            <button onClick={() => setSelectedPost(null)} className="text-gray-300 hover:text-white flex items-center space-x-2 transition">
              <Home className="w-4 h-4" /><span>Home</span>
            </button>
            {isAuthenticated ? (
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2 text-gray-300">
                  <img src={user?.picture} alt={user?.name} className="w-8 h-8 rounded-full" />
                  <span className="text-sm">{user?.name}</span>
                </div>
                <button onClick={logout} className="px-4 py-2 bg-red-500/20 text-red-300 rounded-lg hover:bg-red-500/30 flex items-center space-x-2 transition">
                  <LogOut className="w-4 h-4" /><span>Logout</span>
                </button>
              </div>
            ) : (
              <button onClick={login} className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 flex items-center space-x-2 transition">
                <Lock className="w-4 h-4" /><span>Login</span>
              </button>
            )}
          </nav>
          <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)} className="md:hidden text-white">
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </header>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-black/95 backdrop-blur-md border-b border-purple-500/20 p-4">
          <nav className="flex flex-col space-y-3">
            <button onClick={() => { setSelectedPost(null); setMobileMenuOpen(false); }} className="text-gray-300 hover:text-white flex items-center space-x-2">
              <Home className="w-4 h-4" /><span>Home</span>
            </button>
            {isAuthenticated ? (
              <>
                <div className="flex items-center space-x-2 text-gray-300 py-2">
                  <img src={user?.picture} alt={user?.name} className="w-8 h-8 rounded-full" />
                  <span className="text-sm">{user?.name}</span>
                </div>
                <button onClick={logout} className="px-4 py-2 bg-red-500/20 text-red-300 rounded-lg hover:bg-red-500/30 flex items-center space-x-2">
                  <LogOut className="w-4 h-4" /><span>Logout</span>
                </button>
              </>
            ) : (
              <button onClick={login} className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 flex items-center space-x-2">
                <Lock className="w-4 h-4" /><span>Login</span>
              </button>
            )}
          </nav>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {error && (
          <div className="mb-8 bg-red-500/10 border border-red-500/30 rounded-xl p-4">
            <p className="text-red-300">{error}</p>
            <button
              onClick={fetchThreads}
              className="mt-2 px-4 py-2 bg-red-500/20 text-red-300 rounded-lg hover:bg-red-500/30"
            >
              Retry
            </button>
          </div>
        )}

        {!selectedPost ? (
          <>
            <div className="text-center mb-12">
              <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
                Linux Kernel Patches, <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">Simplified</span>
              </h2>
              <p className="text-xl text-gray-300 mb-8">AI-powered summaries of kernel patches from lore.kernel.org</p>
              <div className="max-w-2xl mx-auto relative">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Search patches by title, tag, or subsystem..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-12 pr-4 py-4 bg-white/10 backdrop-blur-md border border-purple-500/30 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
            </div>

            {loading ? (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
                <p className="text-gray-300 mt-4">Loading patches...</p>
              </div>
            ) : (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredPosts.length === 0 ? (
                  <div className="col-span-full text-center py-12">
                    <p className="text-gray-400 text-lg">No patches found matching your search.</p>
                  </div>
                ) : (
                  filteredPosts.map(post => (
                    <article
                      key={post.id}
                      className="bg-white/5 backdrop-blur-md border border-purple-500/20 rounded-xl p-6 hover:bg-white/10 transition cursor-pointer group"
                      onClick={() => setSelectedPost(post)}
                    >
                      <h3 className="text-xl font-semibold text-white mb-2 group-hover:text-purple-300 transition line-clamp-2">
                        {post.title}
                      </h3>
                      <div className="flex items-center space-x-2 text-sm text-gray-400 mb-3">
                        <User className="w-3 h-3" />
                        <span>{post.author}</span>
                        <span>•</span>
                        <span>{post.date}</span>
                        <span>•</span>
                        <span>{post.emailCount} emails</span>
                      </div>
                      <p className="text-gray-300 mb-4 line-clamp-3">{post.excerpt}</p>
                      <div className="flex flex-wrap gap-2 mb-4">
                        {post.tags.map(tag => (
                          <span key={tag} className="px-3 py-1 bg-purple-500/20 text-purple-300 rounded-full text-xs">
                            {tag}
                          </span>
                        ))}
                        {post.subsystems.map(sub => (
                          <span key={sub} className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded-full text-xs">
                            {sub}
                          </span>
                        ))}
                      </div>
                      {isAuthenticated ? (
                        <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3">
                          <p className="text-sm text-green-300 flex items-start">
                            <Unlock className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                            <span className="italic">{post.simplified}</span>
                          </p>
                        </div>
                      ) : (
                        <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-3 text-center">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              login();
                            }}
                            className="text-sm text-purple-300 hover:text-purple-200 transition"
                          >
                            🔒 Login to see AI summary
                          </button>
                        </div>
                      )}
                    </article>
                  ))
                )}
              </div>
            )}
          </>
        ) : (
          <div className="max-w-4xl mx-auto">
            <button
              onClick={() => setSelectedPost(null)}
              className="mb-6 text-purple-300 hover:text-purple-200 transition flex items-center space-x-2"
            >
              <span>←</span><span>Back to all patches</span>
            </button>
            <article className="bg-white/5 backdrop-blur-md border border-purple-500/20 rounded-xl p-8">
              <h1 className="text-4xl font-bold text-white mb-4">{selectedPost.title}</h1>
              <div className="flex items-center space-x-3 text-gray-400 mb-6">
                <User className="w-4 h-4" />
                <span>{selectedPost.author}</span>
                <span>•</span>
                <span>{selectedPost.date}</span>
                <span>•</span>
                <span>{selectedPost.emailCount} emails in thread</span>
              </div>
              <div className="flex flex-wrap gap-2 mb-6">
                {selectedPost.tags.map(tag => (
                  <span key={tag} className="px-3 py-1 bg-purple-500/20 text-purple-300 rounded-full text-sm">
                    {tag}
                  </span>
                ))}
                {selectedPost.subsystems.map(sub => (
                  <span key={sub} className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded-full text-sm">
                    {sub}
                  </span>
                ))}
              </div>
              {isAuthenticated && (
                <div className="bg-gradient-to-r from-green-500/10 to-blue-500/10 border border-green-500/30 rounded-xl p-6 mb-6">
                  <h3 className="text-lg font-semibold text-green-300 mb-3 flex items-center">
                    <Unlock className="w-5 h-5 mr-2" /> AI-Simplified Explanation
                  </h3>
                  <p className="text-gray-200 text-lg leading-relaxed">{selectedPost.simplified}</p>
                </div>
              )}
              <div className="prose prose-invert max-w-none">
                <p className="text-gray-300 leading-relaxed text-lg">{selectedPost.content}</p>
              </div>
            </article>
          </div>
        )}
      </main>
    </div>
  );
};

export default App;
