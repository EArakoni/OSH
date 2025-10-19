import React, { useState, useEffect } from 'react';
import {
  BookOpen, Home, LogOut, Lock, Menu, X,
  Search, User, Unlock, Sun, Moon
} from 'lucide-react';

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [posts, setPosts] = useState([]);
  const [selectedPost, setSelectedPost] = useState(null);
  const [threadDetails, setThreadDetails] = useState(null);
  const [loadingThread, setLoadingThread] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [darkMode, setDarkMode] = useState(false);

  const auth0Domain = 'dev-gsykrp7lbzxn8prq.us.auth0.com';
  const auth0ClientId = 'rMibqVnfRKY7kSlDeFVNZWdGLRYtXltH';
  const redirectUri = window.location.origin;
  const API_URL = 'http://localhost:5000';

  useEffect(() => {
    fetchThreads();
    checkAuth();
    // Check for saved dark mode preference
    const savedDarkMode = localStorage.getItem('darkMode') === 'true';
    setDarkMode(savedDarkMode);
  }, []);

  const toggleDarkMode = () => {
    const newDarkMode = !darkMode;
    setDarkMode(newDarkMode);
    localStorage.setItem('darkMode', newDarkMode);
  };

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
          excerpt: `Thread with ${thread.email_count} emails about ${thread.subject?.substring(0, 100)}...`,
          tags: thread.tags || [],
          subsystems: thread.subsystems || [],
          simplified: thread.tldr || 'AI summary not available yet.',
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

  const fetchThreadDetails = async (threadId) => {
    setLoadingThread(true);
    try {
      const response = await fetch(`${API_URL}/api/threads/${threadId}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch thread details`);
      }

      const data = await response.json();
      setThreadDetails(data);
    } catch (err) {
      console.error('Error fetching thread details:', err);
      setError(`Failed to load thread details: ${err.message}`);
    } finally {
      setLoadingThread(false);
    }
  };

  const handleThreadClick = (post) => {
    setSelectedPost(post);
    fetchThreadDetails(post.id);
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
    <div className={darkMode ? 'min-h-screen bg-gray-900' : 'min-h-screen bg-gradient-to-br from-gray-50 via-orange-50 to-gray-50'}>
      {/* Header */}
      <header className={darkMode
        ? 'bg-gray-800 border-b border-gray-700 sticky top-0 z-50 shadow-lg'
        : 'bg-white border-b border-gray-200 sticky top-0 z-50 shadow-md'
      }>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg flex items-center justify-center shadow-md">
              <BookOpen className="w-6 h-6 text-white" />
            </div>
            <h1 className={darkMode ? 'text-2xl font-bold text-white' : 'text-2xl font-bold text-gray-900'}>
              KernelPatch<span className="text-orange-600">Digest</span>
            </h1>
          </div>
          <nav className="hidden md:flex items-center space-x-4">
            <button
              onClick={() => setSelectedPost(null)}
              className={darkMode
                ? 'text-gray-300 hover:text-white flex items-center space-x-2 transition px-3 py-2 rounded-lg hover:bg-gray-700'
                : 'text-gray-700 hover:text-gray-900 flex items-center space-x-2 transition px-3 py-2 rounded-lg hover:bg-gray-100'
              }
            >
              <Home className="w-4 h-4" /><span>Home</span>
            </button>

            <button
              onClick={toggleDarkMode}
              className={darkMode
                ? 'p-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-yellow-400 transition'
                : 'p-2 rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-700 transition'
              }
              aria-label="Toggle dark mode"
            >
              {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>

            {isAuthenticated ? (
              <div className="flex items-center space-x-4">
                <div className={darkMode ? 'flex items-center space-x-2 text-gray-300' : 'flex items-center space-x-2 text-gray-700'}>
                  <img src={user?.picture} alt={user?.name} className="w-8 h-8 rounded-full" />
                  <span className="text-sm">{user?.name}</span>
                </div>
                <button
                  onClick={logout}
                  className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 flex items-center space-x-2 transition"
                >
                  <LogOut className="w-4 h-4" /><span>Logout</span>
                </button>
              </div>
            ) : (
              <button
                onClick={login}
                className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 flex items-center space-x-2 transition shadow-md"
              >
                <Lock className="w-4 h-4" /><span>Login</span>
              </button>
            )}
          </nav>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className={darkMode ? 'md:hidden text-white' : 'md:hidden text-gray-900'}
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </header>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className={darkMode ? 'md:hidden bg-gray-800 border-b border-gray-700 p-4' : 'md:hidden bg-white border-b border-gray-200 p-4 shadow-md'}>
          <nav className="flex flex-col space-y-3">
            <button
              onClick={() => { setSelectedPost(null); setMobileMenuOpen(false); }}
              className={darkMode
                ? 'text-gray-300 hover:text-white flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-gray-700'
                : 'text-gray-700 hover:text-gray-900 flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-gray-100'
              }
            >
              <Home className="w-4 h-4" /><span>Home</span>
            </button>

            <button
              onClick={toggleDarkMode}
              className={darkMode
                ? 'flex items-center space-x-2 px-3 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-yellow-400'
                : 'flex items-center space-x-2 px-3 py-2 rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-700'
              }
            >
              {darkMode ? <><Sun className="w-4 h-4" /><span>Light Mode</span></> : <><Moon className="w-4 h-4" /><span>Dark Mode</span></>}
            </button>

            {isAuthenticated ? (
              <>
                <div className={darkMode ? 'flex items-center space-x-2 text-gray-300 py-2' : 'flex items-center space-x-2 text-gray-700 py-2'}>
                  <img src={user?.picture} alt={user?.name} className="w-8 h-8 rounded-full" />
                  <span className="text-sm">{user?.name}</span>
                </div>
                <button
                  onClick={logout}
                  className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 flex items-center space-x-2"
                >
                  <LogOut className="w-4 h-4" /><span>Logout</span>
                </button>
              </>
            ) : (
              <button
                onClick={login}
                className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 flex items-center space-x-2"
              >
                <Lock className="w-4 h-4" /><span>Login</span>
              </button>
            )}
          </nav>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {error && (
          <div className="mb-8 bg-red-50 border border-red-200 rounded-xl p-4">
            <p className="text-red-700">{error}</p>
            <button
              onClick={fetchThreads}
              className="mt-2 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
            >
              Retry
            </button>
          </div>
        )}

        {!selectedPost ? (
          <>
            <div className="text-center mb-12">
              <h2 className={darkMode
                ? 'text-4xl md:text-5xl font-bold text-white mb-4'
                : 'text-4xl md:text-5xl font-bold text-gray-900 mb-4'
              }>
                Linux Kernel Patches, <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-600 to-green-600">Simplified</span>
              </h2>
              <p className={darkMode ? 'text-xl text-gray-300 mb-8' : 'text-xl text-gray-600 mb-8'}>
                AI-powered summaries of kernel patches from lore.kernel.org
              </p>
              <div className="max-w-2xl mx-auto relative">
                <Search className={darkMode ? 'absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5' : 'absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-500 w-5 h-5'} />
                <input
                  type="text"
                  placeholder="Search patches by title, tag, or subsystem..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className={darkMode
                    ? 'w-full pl-12 pr-4 py-4 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-orange-500'
                    : 'w-full pl-12 pr-4 py-4 bg-white border border-gray-300 rounded-xl text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 shadow-sm'
                  }
                />
              </div>
            </div>

            {loading ? (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600"></div>
                <p className={darkMode ? 'text-gray-300 mt-4' : 'text-gray-600 mt-4'}>Loading patches...</p>
              </div>
            ) : (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredPosts.length === 0 ? (
                  <div className="col-span-full text-center py-12">
                    <p className={darkMode ? 'text-gray-400 text-lg' : 'text-gray-500 text-lg'}>No patches found matching your search.</p>
                  </div>
                ) : (
                  filteredPosts.map(post => (
                    <article
                      key={post.id}
                      className={darkMode
                        ? 'bg-gray-800 border border-gray-700 rounded-xl p-6 hover:bg-gray-750 hover:border-orange-500 transition cursor-pointer group shadow-lg'
                        : 'bg-white border border-gray-200 rounded-xl p-6 hover:shadow-xl hover:border-orange-300 transition cursor-pointer group'
                      }
                      onClick={() => handleThreadClick(post)}
                    >
                      <h3 className={darkMode
                        ? 'text-xl font-semibold text-white mb-2 group-hover:text-orange-400 transition line-clamp-2'
                        : 'text-xl font-semibold text-gray-900 mb-2 group-hover:text-orange-600 transition line-clamp-2'
                      }>
                        {post.title}
                      </h3>
                      <div className={darkMode ? 'flex items-center space-x-2 text-sm text-gray-400 mb-3' : 'flex items-center space-x-2 text-sm text-gray-600 mb-3'}>
                        <User className="w-3 h-3" />
                        <span>{post.author}</span>
                        <span>•</span>
                        <span>{post.date}</span>
                        <span>•</span>
                        <span>{post.emailCount} emails</span>
                      </div>
                      <p className={darkMode ? 'text-gray-300 mb-4 line-clamp-3' : 'text-gray-600 mb-4 line-clamp-3'}>{post.excerpt}</p>
                      <div className="flex flex-wrap gap-2 mb-4">
                        {post.tags.map(tag => (
                          <span key={tag} className="px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-xs font-medium">
                            {tag}
                          </span>
                        ))}
                        {post.subsystems.map(sub => (
                          <span key={sub} className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                            {sub}
                          </span>
                        ))}
                      </div>
                      {isAuthenticated ? (
                        <div className={darkMode
                          ? 'bg-green-900/30 border border-green-700 rounded-lg p-3'
                          : 'bg-green-50 border border-green-200 rounded-lg p-3'
                        }>
                          <p className={darkMode ? 'text-sm text-green-300 flex items-start' : 'text-sm text-green-700 flex items-start'}>
                            <Unlock className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                            <span className="italic">{post.simplified}</span>
                          </p>
                        </div>
                      ) : (
                        <div className={darkMode
                          ? 'bg-orange-900/20 border border-orange-700 rounded-lg p-3 text-center'
                          : 'bg-orange-50 border border-orange-200 rounded-lg p-3 text-center'
                        }>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              login();
                            }}
                            className={darkMode
                              ? 'text-sm text-orange-400 hover:text-orange-300 transition'
                              : 'text-sm text-orange-600 hover:text-orange-700 transition font-medium'
                            }
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
              onClick={() => {
                setSelectedPost(null);
                setThreadDetails(null);
              }}
              className={darkMode
                ? 'mb-6 text-orange-400 hover:text-orange-300 transition flex items-center space-x-2'
                : 'mb-6 text-orange-600 hover:text-orange-700 transition flex items-center space-x-2 font-medium'
              }
            >
              <span>←</span><span>Back to all patches</span>
            </button>

            {loadingThread ? (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600"></div>
                <p className={darkMode ? 'text-gray-300 mt-4' : 'text-gray-600 mt-4'}>Loading thread details...</p>
              </div>
            ) : (
              <article className={darkMode ? 'bg-gray-800 border border-gray-700 rounded-xl p-8 shadow-lg' : 'bg-white border border-gray-200 rounded-xl p-8 shadow-md'}>
                <h1 className={darkMode ? 'text-4xl font-bold text-white mb-4' : 'text-4xl font-bold text-gray-900 mb-4'}>{selectedPost.title}</h1>
                <div className={darkMode ? 'flex items-center space-x-3 text-gray-400 mb-6' : 'flex items-center space-x-3 text-gray-600 mb-6'}>
                  <User className="w-4 h-4" />
                  <span>{selectedPost.author}</span>
                  <span>•</span>
                  <span>{selectedPost.date}</span>
                  <span>•</span>
                  <span>{selectedPost.emailCount} emails in thread</span>
                </div>
                <div className="flex flex-wrap gap-2 mb-6">
                  {selectedPost.tags.map(tag => (
                    <span key={tag} className="px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-sm font-medium">
                      {tag}
                    </span>
                  ))}
                  {selectedPost.subsystems.map(sub => (
                    <span key={sub} className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                      {sub}
                    </span>
                  ))}
                </div>

                {/* AI Summary - Always shown */}
                {selectedPost.simplified && (
                  <div className={darkMode
                    ? 'bg-gradient-to-r from-green-900/40 to-green-800/40 border border-green-700 rounded-xl p-6 mb-6'
                    : 'bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl p-6 mb-6'
                  }>
                    <h3 className={darkMode ? 'text-lg font-semibold text-green-300 mb-3 flex items-center' : 'text-lg font-semibold text-green-700 mb-3 flex items-center'}>
                      <Unlock className="w-5 h-5 mr-2" /> AI-Simplified Explanation
                    </h3>
                    <p className={darkMode ? 'text-gray-200 text-lg leading-relaxed' : 'text-gray-700 text-lg leading-relaxed'}>{selectedPost.simplified}</p>
                  </div>
                )}

                {/* Thread Details Tabs */}
                {threadDetails && threadDetails.summary && (
                  <ThreadDetailsTabs
                    summary={threadDetails.summary}
                    emails={threadDetails.emails || []}
                    darkMode={darkMode}
                  />
                )}

                {/* Thread Emails - Simple text display */}
                <div className="mt-8">
                  <h3 className={darkMode ? 'text-2xl font-bold text-white mb-6' : 'text-2xl font-bold text-gray-900 mb-6'}>Email Thread</h3>

                  {threadDetails && threadDetails.emails ? (
                    <div className="space-y-6">
                      {threadDetails.emails.map((email, index) => (
                        <div key={email.id} className={darkMode ? 'bg-gray-900 border border-gray-700 rounded-lg p-6' : 'bg-gray-50 border border-gray-200 rounded-lg p-6'}>
                          <div className="flex items-start justify-between mb-4">
                            <div>
                              <p className={darkMode ? 'text-orange-400 font-semibold' : 'text-orange-600 font-semibold'}>{email.from_address}</p>
                              <p className={darkMode ? 'text-gray-400 text-sm mt-1' : 'text-gray-500 text-sm mt-1'}>{email.date}</p>
                            </div>
                            <span className={darkMode ? 'text-gray-500 text-sm' : 'text-gray-400 text-sm'}>#{index + 1}</span>
                          </div>

                          <h4 className={darkMode ? 'text-white font-medium mb-3' : 'text-gray-900 font-medium mb-3'}>{email.subject}</h4>

                          <pre className={darkMode
                            ? 'text-gray-300 text-sm whitespace-pre-wrap font-mono bg-black/50 p-4 rounded overflow-x-auto'
                            : 'text-gray-700 text-sm whitespace-pre-wrap font-mono bg-white p-4 rounded overflow-x-auto border border-gray-200'
                          }>
                            {email.body}
                          </pre>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className={darkMode ? 'text-gray-400' : 'text-gray-500'}>No email details available.</p>
                  )}
                </div>
              </article>
            )}
          </div>
        )}
      </main>
    </div>
  );
};

// Thread Details Tabs Component
const ThreadDetailsTabs = ({ summary, emails, darkMode }) => {
  const [activeTab, setActiveTab] = useState('overview');

  // Helper function to detect company from email
  const detectCompany = (email) => {
    const domain = email.split('@')[1]?.toLowerCase();
    const personalDomains = ['gmail.com', 'outlook.com', 'yahoo.com', 'hotmail.com', 'protonmail.com'];

    if (personalDomains.includes(domain)) return 'Independent';

    const companyMap = {
      'intel.com': 'Intel',
      'redhat.com': 'Red Hat',
      'linux.dev': 'Linux Foundation',
      'kernel.org': 'Linux Foundation',
      'linuxfoundation.org': 'Linux Foundation',
      'google.com': 'Google',
      'microsoft.com': 'Microsoft',
      'oracle.com': 'Oracle',
      'amd.com': 'AMD',
      'nvidia.com': 'NVIDIA',
      'ibm.com': 'IBM',
    };

    return companyMap[domain] || domain?.split('.')[0] || 'Unknown';
  };

  // Process contributors
  const contributors = {};
  emails.forEach(email => {
    const addr = email.from_address;
    if (!contributors[addr]) {
      contributors[addr] = {
        email: addr,
        count: 0,
        company: detectCompany(addr)
      };
    }
    contributors[addr].count++;
  });

  const topContributors = Object.values(contributors)
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);

  // Get unique companies
  const companies = [...new Set(topContributors.map(c => c.company))];

  // Parse important_changes
  const importantChanges = typeof summary.important_changes === 'string'
    ? JSON.parse(summary.important_changes)
    : summary.important_changes || {};

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'discussion', label: 'Discussion' },
    { id: 'actions', label: 'Action Items' },
    { id: 'contributors', label: 'Contributors' }
  ];

  return (
    <div className={darkMode ? 'bg-gray-800 border border-gray-700 rounded-xl p-6 mb-6' : 'bg-white border border-gray-200 rounded-xl p-6 mb-6'}>
      {/* Tab Headers */}
      <div className="flex space-x-2 border-b border-gray-700 mb-4">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={activeTab === tab.id
              ? 'px-4 py-2 font-medium text-purple-400 border-b-2 border-purple-400'
              : 'px-4 py-2 font-medium text-gray-400 hover:text-gray-300'
            }
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="mt-4">
        {activeTab === 'overview' && (
          <div className="space-y-4">
            {/* Thread Type */}
            {importantChanges.thread_type && (
              <div>
                <h4 className={darkMode ? 'text-sm font-semibold text-gray-400 mb-2' : 'text-sm font-semibold text-gray-600 mb-2'}>Thread Type</h4>
                <span className="inline-block px-3 py-1 bg-purple-500/20 text-purple-300 rounded-full text-sm font-medium">
                  {importantChanges.thread_type.replace('_', ' ').toUpperCase()}
                </span>
              </div>
            )}

            {/* Status */}
            {importantChanges.resolution && (
              <div>
                <h4 className={darkMode ? 'text-sm font-semibold text-gray-400 mb-2' : 'text-sm font-semibold text-gray-600 mb-2'}>Status</h4>
                <p className={darkMode ? 'text-gray-300' : 'text-gray-700'}>{importantChanges.resolution}</p>
              </div>
            )}

            {/* Importance */}
            {summary.importance && (
              <div>
                <h4 className={darkMode ? 'text-sm font-semibold text-gray-400 mb-2' : 'text-sm font-semibold text-gray-600 mb-2'}>Importance</h4>
                <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${summary.importance === 'critical' ? 'bg-red-500/20 text-red-300' :
                    summary.importance === 'high' ? 'bg-orange-500/20 text-orange-300' :
                      summary.importance === 'medium' ? 'bg-yellow-500/20 text-yellow-300' :
                        'bg-green-500/20 text-green-300'
                  }`}>
                  {summary.importance.toUpperCase()}
                </span>
              </div>
            )}

            {/* Activity Metrics */}
            <div>
              <h4 className={darkMode ? 'text-sm font-semibold text-gray-400 mb-2' : 'text-sm font-semibold text-gray-600 mb-2'}>Activity</h4>
              <div className="flex flex-wrap gap-4">
                <div>
                  <span className={darkMode ? 'text-gray-300' : 'text-gray-700'}>{emails.length} emails</span>
                </div>
                <div>
                  <span className={darkMode ? 'text-gray-300' : 'text-gray-700'}>{Object.keys(contributors).length} participants</span>
                </div>
                {emails.length > 0 && (
                  <div>
                    <span className={darkMode ? 'text-gray-300' : 'text-gray-700'}>
                      {emails[0]?.date?.split('T')[0]} → {emails[emails.length - 1]?.date?.split('T')[0]}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Subsystems */}
            {summary.subsystems && summary.subsystems.length > 0 && (
              <div>
                <h4 className={darkMode ? 'text-sm font-semibold text-gray-400 mb-2' : 'text-sm font-semibold text-gray-600 mb-2'}>Subsystems</h4>
                <div className="flex flex-wrap gap-2">
                  {summary.subsystems.map(sub => (
                    <span key={sub} className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                      {sub}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'discussion' && (
          <div className="space-y-4">
            {/* Discussion Summary */}
            {importantChanges.discussion_summary && (
              <div>
                <h4 className={darkMode ? 'text-sm font-semibold text-gray-400 mb-2' : 'text-sm font-semibold text-gray-600 mb-2'}>Discussion Summary</h4>
                <p className={darkMode ? 'text-gray-300 leading-relaxed' : 'text-gray-700 leading-relaxed'}>
                  {importantChanges.discussion_summary}
                </p>
              </div>
            )}

            {/* Key Points */}
            {summary.key_points && summary.key_points.length > 0 && (
              <div>
                <h4 className={darkMode ? 'text-sm font-semibold text-gray-400 mb-2' : 'text-sm font-semibold text-gray-600 mb-2'}>Key Points</h4>
                <ul className="space-y-2">
                  {summary.key_points.map((point, idx) => (
                    <li key={idx} className={darkMode ? 'text-gray-300 flex items-start' : 'text-gray-700 flex items-start'}>
                      <span className="text-purple-400 mr-2">•</span>
                      <span>{point}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {activeTab === 'actions' && (
          <div className="space-y-4">
            {/* Resolution */}
            {importantChanges.resolution && (
              <div>
                <h4 className={darkMode ? 'text-sm font-semibold text-gray-400 mb-2' : 'text-sm font-semibold text-gray-600 mb-2'}>Resolution</h4>
                <p className={darkMode ? 'text-gray-300' : 'text-gray-700'}>{importantChanges.resolution}</p>
              </div>
            )}

            {/* Action Items */}
            {importantChanges.action_items && importantChanges.action_items.length > 0 && (
              <div>
                <h4 className={darkMode ? 'text-sm font-semibold text-gray-400 mb-2' : 'text-sm font-semibold text-gray-600 mb-2'}>Action Items</h4>
                <ul className="space-y-2">
                  {importantChanges.action_items.map((item, idx) => (
                    <li key={idx} className={darkMode ? 'text-gray-300 flex items-start' : 'text-gray-700 flex items-start'}>
                      <span className="text-purple-400 mr-2">□</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {!importantChanges.resolution && (!importantChanges.action_items || importantChanges.action_items.length === 0) && (
              <p className={darkMode ? 'text-gray-400' : 'text-gray-500'}>No action items or resolution available.</p>
            )}
          </div>
        )}

        {activeTab === 'contributors' && (
          <div className="space-y-4">
            {/* Top Contributors */}
            <div>
              <h4 className={darkMode ? 'text-sm font-semibold text-gray-400 mb-2' : 'text-sm font-semibold text-gray-600 mb-2'}>
                Top Contributors ({topContributors.length})
              </h4>
              <div className="space-y-2">
                {topContributors.map((contrib, idx) => (
                  <div key={idx} className={darkMode ? 'flex justify-between items-center py-2 border-b border-gray-700' : 'flex justify-between items-center py-2 border-b border-gray-200'}>
                    <div>
                      <p className={darkMode ? 'text-gray-300 text-sm' : 'text-gray-700 text-sm'}>{contrib.email}</p>
                      <p className={darkMode ? 'text-gray-500 text-xs' : 'text-gray-500 text-xs'}>{contrib.company}</p>
                    </div>
                    <span className={darkMode ? 'text-purple-400 font-medium' : 'text-purple-600 font-medium'}>
                      {contrib.count} {contrib.count === 1 ? 'email' : 'emails'}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Companies */}
            {companies.length > 0 && (
              <div>
                <h4 className={darkMode ? 'text-sm font-semibold text-gray-400 mb-2' : 'text-sm font-semibold text-gray-600 mb-2'}>
                  Organizations ({companies.length})
                </h4>
                <div className="flex flex-wrap gap-2">
                  {companies.map((company, idx) => (
                    <span key={idx} className="px-3 py-1 bg-purple-500/20 text-purple-300 rounded-full text-sm">
                      {company}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
