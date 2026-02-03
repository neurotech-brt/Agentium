import { useState, useEffect } from 'react';
import { Users, CheckCircle, XCircle, Trash2, Key, Shield, Clock, Loader2 } from 'lucide-react';
import { api } from '@/services/api';
import toast from 'react-hot-toast';

interface PendingUser {
    id: string;
    username: string;
    created_at: string;
    status: 'pending' | 'approved' | 'rejected';
}

interface ApprovedUser {
    id: string;
    username: string;
    role: string;
    agentium_id?: string;
    created_at: string;
    is_active: boolean;
}

export default function UserManagement() {
    const [pendingUsers, setPendingUsers] = useState<PendingUser[]>([]);
    const [approvedUsers, setApprovedUsers] = useState<ApprovedUser[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'pending' | 'approved'>('pending');

    // Change password modal state
    const [showPasswordModal, setShowPasswordModal] = useState(false);
    const [selectedUser, setSelectedUser] = useState<ApprovedUser | null>(null);
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');

    useEffect(() => {
        fetchUsers();
    }, []);

    const fetchUsers = async () => {
        setLoading(true);
        try {
            const [pendingRes, approvedRes] = await Promise.all([
                api.get('/api/v1/admin/users/pending'),
                api.get('/api/v1/admin/users')
            ]);

            setPendingUsers(pendingRes.data);
            setApprovedUsers(approvedRes.data);
        } catch (error: any) {
            toast.error('Failed to fetch users');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async (userId: string) => {
        try {
            await api.post(`/api/v1/admin/users/${userId}/approve`);
            toast.success('User approved successfully');
            fetchUsers();
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Failed to approve user');
        }
    };

    const handleReject = async (userId: string) => {
        if (!confirm('Are you sure you want to reject this user request?')) return;

        try {
            await api.post(`/api/v1/admin/users/${userId}/reject`);
            toast.success('User request rejected');
            fetchUsers();
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Failed to reject user');
        }
    };

    const handleDelete = async (userId: string, username: string) => {
        if (!confirm(`Are you sure you want to delete user "${username}"? This action cannot be undone.`)) return;

        try {
            await api.delete(`/api/v1/admin/users/${userId}`);
            toast.success('User deleted successfully');
            fetchUsers();
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Failed to delete user');
        }
    };

    const handleChangePassword = async () => {
        if (!selectedUser) return;

        if (newPassword !== confirmPassword) {
            toast.error('Passwords do not match');
            return;
        }

        if (newPassword.length < 6) {
            toast.error('Password must be at least 6 characters');
            return;
        }

        try {
            await api.post(`/api/v1/admin/users/${selectedUser.id}/change-password`, {
                new_password: newPassword
            });
            toast.success('Password changed successfully');
            setShowPasswordModal(false);
            setSelectedUser(null);
            setNewPassword('');
            setConfirmPassword('');
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Failed to change password');
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center p-8">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                        <Users className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                            User Management
                        </h2>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                            Manage user access and permissions
                        </p>
                    </div>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-2 border-b border-gray-200 dark:border-gray-700">
                <button
                    onClick={() => setActiveTab('pending')}
                    className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${activeTab === 'pending'
                        ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                        : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                        }`}
                >
                    Pending Requests ({pendingUsers.length})
                </button>
                <button
                    onClick={() => setActiveTab('approved')}
                    className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${activeTab === 'approved'
                        ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                        : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                        }`}
                >
                    Approved Users ({approvedUsers.length})
                </button>
            </div>

            {/* Pending Users Tab */}
            {activeTab === 'pending' && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
                    {pendingUsers.length === 0 ? (
                        <div className="p-8 text-center">
                            <Clock className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                            <p className="text-gray-600 dark:text-gray-400">No pending user requests</p>
                        </div>
                    ) : (
                        <div className="divide-y divide-gray-200 dark:divide-gray-700">
                            {pendingUsers.map((user) => (
                                <div key={user.id} className="p-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 rounded-full bg-yellow-100 dark:bg-yellow-900/30 flex items-center justify-center">
                                            <Users className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
                                        </div>
                                        <div>
                                            <p className="font-medium text-gray-900 dark:text-white">
                                                {user.username}
                                            </p>
                                            <p className="text-sm text-gray-600 dark:text-gray-400">
                                                Requested: {formatDate(user.created_at)}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => handleApprove(user.id)}
                                            className="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors"
                                        >
                                            <CheckCircle className="w-4 h-4" />
                                            Approve
                                        </button>
                                        <button
                                            onClick={() => handleReject(user.id)}
                                            className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors"
                                        >
                                            <XCircle className="w-4 h-4" />
                                            Reject
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Approved Users Tab */}
            {activeTab === 'approved' && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
                    {approvedUsers.length === 0 ? (
                        <div className="p-8 text-center">
                            <Users className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                            <p className="text-gray-600 dark:text-gray-400">No approved users</p>
                        </div>
                    ) : (
                        <div className="divide-y divide-gray-200 dark:divide-gray-700">
                            {approvedUsers.map((user) => (
                                <div key={user.id} className="p-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                                            <Users className="w-5 h-5 text-green-600 dark:text-green-400" />
                                        </div>
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <p className="font-medium text-gray-900 dark:text-white">
                                                    {user.username}
                                                </p>
                                                {user.agentium_id?.startsWith('0') && (
                                                    <Shield
                                                        className="w-4 h-4 text-yellow-600"
                                                        aria-label="Admin"
                                                    />
                                                )}
                                            </div>
                                            <p className="text-sm text-gray-600 dark:text-gray-400">
                                                Role: {user.role} {user.agentium_id && `• ID: ${user.agentium_id}`}
                                            </p>
                                            <p className="text-xs text-gray-500 dark:text-gray-500">
                                                Joined: {formatDate(user.created_at)}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => {
                                                setSelectedUser(user);
                                                setShowPasswordModal(true);
                                            }}
                                            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors"
                                        >
                                            <Key className="w-4 h-4" />
                                            Change Password
                                        </button>
                                        <button
                                            onClick={() => handleDelete(user.id, user.username)}
                                            className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                            Delete
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Change Password Modal */}
            {showPasswordModal && selectedUser && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-md w-full p-6">
                        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                            Change Password for {selectedUser.username}
                        </h3>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    New Password
                                </label>
                                <input
                                    type="password"
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                                    placeholder="Enter new password"
                                    minLength={6}
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    Confirm Password
                                </label>
                                <input
                                    type="password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                                    placeholder="Confirm new password"
                                    minLength={6}
                                />
                            </div>
                        </div>

                        <div className="flex gap-3 mt-6">
                            <button
                                onClick={() => {
                                    setShowPasswordModal(false);
                                    setSelectedUser(null);
                                    setNewPassword('');
                                    setConfirmPassword('');
                                }}
                                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleChangePassword}
                                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
                            >
                                Change Password
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}