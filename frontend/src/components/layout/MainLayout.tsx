// src/components/layout/MainLayout.tsx
import { useAuthStore } from '@/store/authStore';
import { useWebSocketStore } from '@/store/websocketStore';
import { NavLink, useNavigate, useLocation, useOutlet } from 'react-router-dom';
import {
    LayoutDashboard,
    Crown,
    Users,
    ClipboardList,
    Activity,
    BookOpen,
    Settings,
    LogOut,
    Cpu,
    Radio,
    Shield,
    Gavel,
    Inbox,
    FlaskConical,
} from 'lucide-react';
import { useState, useRef, useCallback, Suspense } from 'react';
// ── Voice Bridge addition ─────────────────────────────────────────────────────
import { VoiceIndicator } from '@/components/VoiceIndicator';

// ── KeepAliveOutlet ───────────────────────────────────────────────────────────
// Replaces AnimatePresence + motion.div. Instead of unmounting the previous
// page and mounting the next one (which caused the full-screen flicker from two
// absolutely-positioned divs overlapping during a crossfade), we keep every
// visited page mounted and simply toggle visibility via opacity + pointer-events.
//
// Why this eliminates the flicker:
//   • Only one div is ever opaque at a time — no overlapping paint.
//   • Pages are never unmounted, so returning to a tab is instantaneous with
//     zero re-fetch or loading-skeleton flash.
//   • CSS opacity transition handles the fade; no JS animation frame budget used.
function KeepAliveOutlet() {
    const location = useLocation();
    const currentOutlet = useOutlet();

    // Cache React elements keyed by pathname. Once a page is first rendered its
    // element stays in the map for the lifetime of the layout, keeping the
    // component tree alive even when the route is not active.
    const cache = useRef<Map<string, React.ReactNode>>(new Map());
    if (currentOutlet) {
        cache.current.set(location.pathname, currentOutlet);
    }

    return (
        <>
            {Array.from(cache.current.entries()).map(([path, outlet]) => {
                const isActive = path === location.pathname;
                return (
                    <div
                        key={path}
                        style={{
                            position: 'absolute',
                            inset: 0,
                            overflowY: 'auto',
                            // Inactive pages are invisible and non-interactive but
                            // remain mounted — no re-mount cost on revisit.
                            opacity: isActive ? 1 : 0,
                            pointerEvents: isActive ? 'auto' : 'none',
                            transition: 'opacity 0.15s ease',
                        }}
                    >
                        {outlet}
                    </div>
                );
            })}
        </>
    );
}

// ── PageSkeleton ──────────────────────────────────────────────────────────────
// Shown only on the very first visit to a lazy page while its JS chunk loads.
// Subsequent visits hit KeepAliveOutlet's cache and never render this at all.
// Deliberately low-contrast so it doesn't flash aggressively in dark mode.
function PageSkeleton() {
    return (
        <div className="absolute inset-0 flex flex-col gap-4 p-6 overflow-hidden">
            {/* Simulated page header */}
            <div className="h-8 w-48 rounded-lg bg-gray-200 dark:bg-white/5 animate-pulse" />
            {/* Simulated content rows */}
            <div className="flex flex-col gap-3 mt-2">
                {[100, 85, 92, 78].map((w, i) => (
                    <div
                        key={i}
                        className="h-4 rounded-md bg-gray-200 dark:bg-white/5 animate-pulse"
                        style={{ width: `${w}%`, animationDelay: `${i * 60}ms` }}
                    />
                ))}
            </div>
            {/* Simulated card grid */}
            <div className="grid grid-cols-3 gap-4 mt-4">
                {[0, 1, 2].map(i => (
                    <div
                        key={i}
                        className="h-32 rounded-xl bg-gray-200 dark:bg-white/5 animate-pulse"
                        style={{ animationDelay: `${i * 80}ms` }}
                    />
                ))}
            </div>
        </div>
    );
}
export function MainLayout() {
    const { user, logout } = useAuthStore();
    const navigate = useNavigate();
    const unreadCount = useWebSocketStore(state => state.unreadCount);
    const [isDark, setIsDark] = useState(() => {
        if (typeof window !== 'undefined') {
            return document.documentElement.classList.contains('dark');
        }
        return false;
    });
    // Updated: Check both isSovereign and is_admin
    const isAdmin = user?.isSovereign || user?.is_admin || false;

    const handleLogout = () => {
        window.dispatchEvent(new Event('logout'));
        logout();
        navigate('/login');
    };

    const toggleTheme = () => {
        const newDark = !isDark;
        setIsDark(newDark);
        if (newDark) {
            document.documentElement.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.classList.remove('dark');
            localStorage.setItem('theme', 'light');
        }
    };

    // ── Hover prefetch ────────────────────────────────────────────────────────
    // Triggers the dynamic import for a page's JS chunk on nav-link hover so
    // that by the time the user clicks, the chunk is already in the browser
    // cache. Wrapped in useCallback so the function reference is stable.
    const prefetch = useCallback((path: string) => {
        switch (path) {
            case '/chat':         import('@/pages/ChatPage');         break;
            case '/agents':       import('@/pages/AgentsPage');       break;
            case '/tasks':        import('@/pages/TasksPage');        break;
            case '/monitoring':   import('@/pages/MonitoringPage');   break;
            case '/voting':       import('@/pages/VotingPage');       break;
            case '/constitution': import('@/pages/ConstitutionPage'); break;
            case '/models':       import('@/pages/ModelsPage');       break;
            case '/channels':     import('@/pages/ChannelsPage');     break;
            case '/message-log':  import('@/pages/MessageLogPage');   break;
            case '/ab-testing':   import('@/pages/ABTestingPage');    break;
            case '/settings':     import('@/pages/SettingsPage');     break;
            case '/sovereign':    import('@/pages/SovereignDashboard'); break;
            default:              import('@/pages/Dashboard');        break;
        }
    }, []);

    type NavItem = {
        path: string;
        label: string;
        icon: React.ComponentType<{ className?: string }>;
        badge?: number;
        variant?: 'default' | 'danger';
        adminOnly?: boolean;
    };

    const navItems: NavItem[] = [
        { path: '/', label: 'Dashboard', icon: LayoutDashboard },
        {
            path: '/chat',
            label: 'Command Interface',
            icon: Crown,
            badge: unreadCount > 0 ? unreadCount : undefined,
        },
        { path: '/agents', label: 'Agents', icon: Users },
        { path: '/tasks', label: 'Tasks', icon: ClipboardList },
        { path: '/monitoring', label: 'Monitoring', icon: Activity },
        { path: '/voting', label: 'Voting', icon: Gavel },
        { path: '/constitution', label: 'Constitution', icon: BookOpen },
        { path: '/models', label: 'Models', icon: Cpu },
        { path: '/channels', label: 'Channels', icon: Radio },
        { path: '/message-log', label: 'Message Log', icon: Inbox },
        { path: '/ab-testing', label: 'A/B Testing', icon: FlaskConical, adminOnly: true },
        { path: '/settings', label: 'Settings', icon: Settings },
        ...(isAdmin
            ? [{ path: '/sovereign', label: 'Sovereign Control', icon: Shield, variant: 'danger' as const }]
            : []),
    ];

    // Filter nav items based on admin status
    const visibleNavItems = navItems.filter(item => !item.adminOnly || isAdmin);

    return (
        <div className="h-screen bg-gray-50 dark:bg-[#0f1117] flex">
            <aside className="w-64 bg-white dark:bg-[#161b27] border-r border-gray-200 dark:border-[#1e2535] flex flex-col">
                {/* Header */}
                <div className="px-4 py-3 border-b border-gray-200 dark:border-[#1e2535] flex-shrink-0">
                    <div className="flex items-center gap-2">
                        <button
                            onClick={toggleTheme}
                            className="group relative p-2 rounded-xl transition-all duration-300 hover:bg-gray-100 dark:hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                            aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
                            title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
                        >
                            <Shield className="w-8 h-8 text-blue-600 transition-all duration-300 rotate-0 scale-100 dark:rotate-90 dark:scale-0 dark:opacity-0" />
                            <Shield className="w-8 h-8 absolute inset-0 m-auto text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.5)] transition-all duration-300 rotate-90 scale-0 opacity-0 dark:rotate-0 dark:scale-100 dark:opacity-100" />
                        </button>
                        <div>
                            <h1 className="text-xl font-bold text-gray-900 dark:text-white">Agentium</h1>
                            <p className="text-xs text-gray-500 dark:text-blue-400/70">AI Governance</p>
                        </div>
                    </div>
                </div>

                {/* Navigation */}
                <nav className="flex-1 px-3 py-2 space-y-0.5 overflow-y-hidden">
                    {visibleNavItems.map((item) => (
                        <div key={item.path}>
                            {item.variant === 'danger' && (
                                <div className="my-1.5 border-t border-gray-200 dark:border-[#1e2535]" />
                            )}
                            <NavLink
                                to={item.path}
                                end={item.path === '/'}
                                onMouseEnter={() => prefetch(item.path)}
                                className={({ isActive }) =>
                                    `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                                        item.variant === 'danger'
                                            ? isActive
                                                ? 'bg-red-50 text-red-700 dark:bg-red-500/10 dark:text-red-300 border border-red-200 dark:border-red-500/20'
                                                : 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 bg-red-50/50 dark:bg-red-500/5'
                                            : isActive
                                                ? 'bg-blue-50 text-blue-700 dark:bg-blue-500/10 dark:text-blue-300'
                                                : 'text-gray-700 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-white/5'
                                    }`
                                }
                            >
                                <item.icon className={`w-[18px] h-[18px] flex-shrink-0 ${item.variant === 'danger' ? 'text-red-500' : ''}`} />
                                <span className="flex-1">{item.label}</span>
                                {item.badge !== undefined && (
                                    <span className="bg-red-500 text-white text-xs font-bold px-1.5 py-0.5 rounded-full min-w-[18px] text-center">
                                        {item.badge > 9 ? '9+' : item.badge}
                                    </span>
                                )}
                            </NavLink>
                        </div>
                    ))}
                </nav>

                {/* User section */}
                <div className="px-4 py-3 border-t border-gray-200 dark:border-[#1e2535]">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white text-sm font-bold">
                            {user?.username?.charAt(0).toUpperCase() || 'U'}
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                                {user?.username || 'User'}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                                {user?.role || 'Member'}
                            </p>
                        </div>
                        {/* ── Voice Bridge status indicator (icon only) ── */}
                        <VoiceIndicator iconOnly />
                    </div>

                    <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-lg transition-colors"
                    >
                        <LogOut className="w-4 h-4" />
                        Logout
                    </button>
                </div>
            </aside>

            {/* Main content — position:relative is required so the absolutely-
                positioned KeepAliveOutlet fills this container correctly.
                Suspense is intentionally placed HERE (not in App.tsx) so that
                when a lazy page chunk suspends on first visit, only this content
                pane shows the skeleton — the sidebar and nav stay mounted and
                visible, eliminating the full-layout flicker.                   */}
            <main className="flex-1 min-h-0 overflow-hidden relative">
                <Suspense fallback={<PageSkeleton />}>
                    <KeepAliveOutlet />
                </Suspense>
            </main>
        </div>
    );
}