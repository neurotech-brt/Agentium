import { useState, useEffect } from 'react';
import { 
    Users, 
    CheckCircle, 
    XCircle, 
    Trash2, 
    Key, 
    Shield, 
    Clock, 
    Loader2, 
    UserCheck, 
    UserX,
    Mail,
    Calendar,
    AlertCircle,
    Search,
    Filter
} from 'lucide-react';
import { api } from '@/services/api';
import toast from 'react-hot-toast';
import { useAuthStore } from '@/store/authStore';

interface User {
    id: number;
    username: string;
    email: string;
    is_active: boolean;
    is_admin: boolean;
    is_pending: boolean;
    created_at?: string;
    updated_at?: string;
}

interface UserListResponse {
    users: User[];
    total: number;
}

export default function UserManagement() {
    const { user: currentUser } = useAuthStore();
    const [pendingUsers, setPendingUsers] = useState<User[]>([]);
    const [approvedUsers, setApprovedUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'pending' | 'approved'>('pending');
    const [showPasswordModal, setShowPasswordModal] = useState(false);
    const [selectedUser, setSelectedUser] = useState<User | null>(null);
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        fetchUsers();
    }, []);

    // Admin access control
    if (!currentUser?.is_admin) {
        return (
            <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-6">
                <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 p-8 text-center max-w-md">
                    <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mx-auto mb-4">
                        <Shield className="w-8 h-8 text-red-600 dark:text-red-400" />
                    </div>
                    <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                        Access Denied
                    </h2>
                    <p className="text-gray-600 dark:text-gray-400">
                        Admin privileges required to access user management.
                    </p>
                </div>
            </div>
        );
    }

    const fetchUsers = async () => {
        setLoading(true);
        try {
            const [pendingRes, approvedRes] = await Promise.all([
                api.get<UserListResponse>('/api/v1/admin/users/pending'),
                api.get<UserListResponse>('/api/v1/admin/users')
            ]);

            setPendingUsers(pendingRes.data.users || []);
            setApprovedUsers(approvedRes.data.users || []);
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Failed to fetch users');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async (userId: number, username: string) => {
        try {
            await api.post(`/api/v1/admin/users/${userId}/approve`);
            toast.success(`${username} approved successfully`, {
                icon: '✅',
                duration: 3000
            });
            fetchUsers();
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Failed to approve user');
        }
    };

    const handleReject = async (userId: number, username: string) => {
        if (!confirm(`Are you sure you want to reject ${username}'s signup request?`)) return;

        try {
            await api.post(`/api/v1/admin/users/${userId}/reject`);
            toast.success(`${username}'s request rejected`, {
                icon: '❌',
                duration: 3000
            });
            fetchUsers();
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Failed to reject user');
        }
    };

    const handleDelete = async (userId: number, username: string) => {
        if (!confirm(`Delete user "${username}"? This action cannot be undone.`)) return;

        if (userId === currentUser.id) {
            toast.error('You cannot delete your own account');
            return;
        }

        try {
            await api.delete(`/api/v1/admin/users/${userId}`);
            toast.success(`${username} deleted successfully`);
            fetchUsers();
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Failed to delete user');
        }
    };

    const handleChangePassword = async () => {
        if (!selectedUser || !newPassword) return;

        if (newPassword !== confirmPassword) {
            toast.error('Passwords do not match');
            return;
        }

        if (newPassword.length < 8) {
            toast.error('Password must be at least 8 characters');
            return;
        }

        try {
            await api.post(`/api/v1/admin/users/${selectedUser.id}/change-password`, {
                new_password: newPassword
            });
            toast.success(`Password changed for ${selectedUser.username}`, {
                icon: '🔐',
                duration: 3000
            });
            setShowPasswordModal(false);
            setSelectedUser(null);
            setNewPassword('');
            setConfirmPassword('');
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Failed to change password');
        }
    };

    const formatDate = (dateString?: string) => {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    // Filter users based on search
    const filteredApprovedUsers = approvedUsers.filter(user => 
        user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
        user.email.toLowerCase().includes(searchQuery.toLowerCase())
    );

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
                <div className="flex flex-col items-center gap-3">
                    <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
                    <span className="text-sm text-gray-500 dark:text-gray-400">Loading users...</span>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <div className="flex items-center gap-3 mb-3">
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center shadow-lg">
                            <Users className="w-7 h-7 text-white" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                                User Management
                            </h1>
                            <p className="text-gray-600 dark:text-gray-400 text-sm">
                                Manage user approvals and permissions
                            </p>
                        </div>
                    </div>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Pending Approvals</p>
                                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                                    {pendingUsers.length}
                                </p>
                            </div>
                            <div className="w-12 h-12 rounded-lg bg-yellow-100 dark:bg-yellow-900/30 flex items-center justify-center">
                                <Clock className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
                            </div>
                        </div>
                    </div>

                    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Active Users</p>
                                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                                    {approvedUsers.filter(u => u.is_active).length}
                                </p>
                            </div>
                            <div className="w-12 h-12 rounded-lg bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                                <UserCheck className="w-6 h-6 text-green-600 dark:text-green-400" />
                            </div>
                        </div>
                    </div>

                    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Total Users</p>
                                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                                    {approvedUsers.length}
                                </p>
                            </div>
                            <div className="w-12 h-12 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                                <Users className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex gap-2 mb-6">
                    <button
                        onClick={() => setActiveTab('pending')}
                        className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                            activeTab === 'pending'
                                ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
                                : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                        }`}
                    >
                        <div className="flex items-center gap-2">
                            <Clock className="w-5 h-5" />
                            Pending Approvals
                            {pendingUsers.length > 0 && (
                                <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                                    activeTab === 'pending' 
                                        ? 'bg-white/20 text-white' 
                                        : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                                }`}>
                                    {pendingUsers.length}
                                </span>
                            )}
                        </div>
                    </button>
                    <button
                        onClick={() => setActiveTab('approved')}
                        className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                            activeTab === 'approved'
                                ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
                                : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                        }`}
                    >
                        <div className="flex items-center gap-2">
                            <UserCheck className="w-5 h-5" />
                            Approved Users
                        </div>
                    </button>
                </div>

                {/* Pending Users Tab */}
                {activeTab === 'pending' && (
                    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                        {pendingUsers.length === 0 ? (
                            <div className="p-12 text-center">
                                <div className="w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center mx-auto mb-4">
                                    <Clock className="w-8 h-8 text-gray-400 dark:text-gray-500" />
                                </div>
                                <p className="text-gray-900 dark:text-white font-medium mb-1">No Pending Approvals</p>
                                <p className="text-sm text-gray-500 dark:text-gray-400">
                                    All signup requests have been processed
                                </p>
                            </div>
                        ) : (
                            <div className="divide-y divide-gray-200 dark:divide-gray-700">
                                {pendingUsers.map((user) => (
                                    <div 
                                        key={user.id} 
                                        className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                                    >
                                        <div className="flex items-start justify-between gap-4">
                                            <div className="flex items-start gap-4 flex-1">
                                                <div className="w-14 h-14 rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center flex-shrink-0 shadow-lg">
                                                    <Users className="w-7 h-7 text-white" />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                                                            {user.username}
                                                        </h3>
                                                        <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400">
                                                            Pending
                                                        </span>
                                                    </div>
                                                    <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                                                        <div className="flex items-center gap-1.5">
                                                            <Mail className="w-4 h-4" />
                                                            {user.email}
                                                        </div>
                                                        <div className="flex items-center gap-1.5">
                                                            <Calendar className="w-4 h-4" />
                                                            {formatDate(user.created_at)}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="flex gap-2 flex-shrink-0">
                                                <button
                                                    onClick={() => handleApprove(user.id, user.username)}
                                                    className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-semibold rounded-lg flex items-center gap-2 transition-all shadow-sm hover:shadow-md"
                                                >
                                                    <CheckCircle className="w-4 h-4" />
                                                    Approve
                                                </button>
                                                <button
                                                    onClick={() => handleReject(user.id, user.username)}
                                                    className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-semibold rounded-lg flex items-center gap-2 transition-all shadow-sm hover:shadow-md"
                                                >
                                                    <XCircle className="w-4 h-4" />
                                                    Reject
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Approved Users Tab */}
                {activeTab === 'approved' && (
                    <>
                        {/* Search Bar */}
                        <div className="mb-6">
                            <div className="relative">
                                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                <input
                                    type="text"
                                    placeholder="Search users by name or email..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="w-full pl-12 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                                />
                            </div>
                        </div>

                        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                            {filteredApprovedUsers.length === 0 ? (
                                <div className="p-12 text-center">
                                    <div className="w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center mx-auto mb-4">
                                        <Users className="w-8 h-8 text-gray-400 dark:text-gray-500" />
                                    </div>
                                    <p className="text-gray-900 dark:text-white font-medium mb-1">
                                        {searchQuery ? 'No Users Found' : 'No Approved Users'}
                                    </p>
                                    <p className="text-sm text-gray-500 dark:text-gray-400">
                                        {searchQuery ? 'Try a different search term' : 'Approve pending users to get started'}
                                    </p>
                                </div>
                            ) : (
                                <div className="divide-y divide-gray-200 dark:divide-gray-700">
                                    {filteredApprovedUsers.map((user) => (
                                        <div 
                                            key={user.id} 
                                            className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                                        >
                                            <div className="flex items-start justify-between gap-4">
                                                <div className="flex items-start gap-4 flex-1">
                                                    <div className={`w-14 h-14 rounded-full flex items-center justify-center flex-shrink-0 shadow-lg ${
                                                        user.is_admin 
                                                            ? 'bg-gradient-to-br from-purple-500 to-pink-500' 
                                                            : 'bg-gradient-to-br from-blue-500 to-cyan-500'
                                                    }`}>
                                                        {user.is_admin ? (
                                                            <Shield className="w-7 h-7 text-white" />
                                                        ) : (
                                                            <Users className="w-7 h-7 text-white" />
                                                        )}
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <div className="flex items-center gap-2 mb-2">
                                                            <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                                                                {user.username}
                                                            </h3>
                                                            {user.is_admin && (
                                                                <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400 flex items-center gap-1">
                                                                    <Shield className="w-3 h-3" />
                                                                    Admin
                                                                </span>
                                                            )}
                                                            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                                                                user.is_active
                                                                    ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                                                                    : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-400'
                                                            }`}>
                                                                {user.is_active ? 'Active' : 'Inactive'}
                                                            </span>
                                                        </div>
                                                        <div className="space-y-1">
                                                            <div className="flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-400">
                                                                <Mail className="w-4 h-4" />
                                                                {user.email}
                                                            </div>
                                                            <div className="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-500">
                                                                <Calendar className="w-4 h-4" />
                                                                Joined {formatDate(user.created_at)}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex gap-2 flex-shrink-0">
                                                    <button
                                                        onClick={() => {
                                                            setSelectedUser(user);
                                                            setShowPasswordModal(true);
                                                        }}
                                                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg flex items-center gap-2 transition-all shadow-sm hover:shadow-md"
                                                    >
                                                        <Key className="w-4 h-4" />
                                                        Password
                                                    </button>
                                                    <button
                                                        onClick={() => handleDelete(user.id, user.username)}
                                                        disabled={user.id === currentUser.id}
                                                        className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold rounded-lg flex items-center gap-2 transition-all shadow-sm hover:shadow-md"
                                                        title={user.id === currentUser.id ? 'Cannot delete your own account' : ''}
                                                    >
                                                        <Trash2 className="w-4 h-4" />
                                                        Delete
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </>
                )}

                {/* Password Change Modal */}
                {showPasswordModal && selectedUser && (
                    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-in fade-in duration-200">
                        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-md w-full border border-gray-200 dark:border-gray-700 animate-in zoom-in duration-200">
                            {/* Modal Header */}
                            <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-800 dark:to-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-5">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center">
                                        <Key className="w-5 h-5 text-white" />
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                                            Change Password
                                        </h3>
                                        <p className="text-sm text-gray-600 dark:text-gray-400">
                                            for {selectedUser.username}
                                        </p>
                                    </div>
                                </div>
                            </div>

                            {/* Modal Body */}
                            <div className="p-6 space-y-5">
                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                                        New Password
                                    </label>
                                    <input
                                        type="password"
                                        value={newPassword}
                                        onChange={(e) => setNewPassword(e.target.value)}
                                        className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                                        placeholder="Enter new password"
                                        minLength={8}
                                    />
                                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1.5">
                                        Minimum 8 characters
                                    </p>
                                </div>

                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                                        Confirm Password
                                    </label>
                                    <input
                                        type="password"
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                                        placeholder="Confirm new password"
                                        minLength={8}
                                    />
                                </div>

                                {newPassword && confirmPassword && newPassword !== confirmPassword && (
                                    <div className="flex items-center gap-2 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
                                        <AlertCircle className="w-4 h-4 flex-shrink-0" />
                                        Passwords do not match
                                    </div>
                                )}
                            </div>

                            {/* Modal Footer */}
                            <div className="flex gap-3 px-6 pb-6">
                                <button
                                    onClick={() => {
                                        setShowPasswordModal(false);
                                        setSelectedUser(null);
                                        setNewPassword('');
                                        setConfirmPassword('');
                                    }}
                                    className="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-semibold rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleChangePassword}
                                    disabled={!newPassword || newPassword !== confirmPassword || newPassword.length < 8}
                                    className="flex-1 px-4 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-all shadow-lg hover:shadow-xl"
                                >
                                    Change Password
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
