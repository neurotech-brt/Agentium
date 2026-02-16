// src/pages/SignupPage.tsx
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { AlertCircle, Loader2, CheckCircle, ArrowLeft } from 'lucide-react';
import { api } from '@/services/api';
import toast from 'react-hot-toast';

export function SignupPage() {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        // Validation
        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        if (password.length < 8) {
            setError('Password must be at least 8 characters long');
            return;
        }

        // Basic email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            setError('Please enter a valid email address');
            return;
        }

        setIsLoading(true);

        try {
            // Send request matching backend SignupRequest model
            const response = await api.post('/api/v1/auth/signup', { 
                username, 
                email,
                password 
            });
            
            // Check if response was successful
            if (response.data.success) {
                setSuccess(true);
                toast.success('Signup request submitted! Awaiting admin approval.', {
                    duration: 4000,
                    icon: '✅'
                });
                setTimeout(() => navigate('/login'), 3000);
            } else {
                throw new Error(response.data.message || 'Signup failed');
            }
        } catch (error: any) {
            console.error('Signup error:', error);
            
            // Handle different error formats
            let errorMsg = 'Signup failed. Please try again.';
            
            if (error.response?.data?.detail) {
                // FastAPI validation error format
                if (Array.isArray(error.response.data.detail)) {
                    errorMsg = error.response.data.detail
                        .map((err: any) => `${err.loc?.join(' ')} - ${err.msg}`)
                        .join(', ');
                } else if (typeof error.response.data.detail === 'string') {
                    errorMsg = error.response.data.detail;
                }
            } else if (error.message) {
                errorMsg = error.message;
            }
            
            setError(errorMsg);
            toast.error(errorMsg, { duration: 4000 });
        } finally {
            setIsLoading(false);
        }
    };

    if (success) {
        return (
            <>
                {/* Success Card */}
                <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 p-8 text-center backdrop-blur-sm">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30 mb-4">
                        <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                        Request Submitted!
                    </h2>
                    <p className="text-gray-600 dark:text-gray-400 mb-6">
                        Your signup request has been sent to the admin for approval.
                        You will be able to login once approved.
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-500">
                        Redirecting to login page...
                    </p>
                </div>
            </>
        );
    }

    return (
        <>
            {/* Signup Card - Same structure as Login */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 p-8 backdrop-blur-sm">
                <div className="mb-6">
                    <Link 
                        to="/login" 
                        className="inline-flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400 hover:underline mb-4 transition-colors"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Back to Login
                    </Link>
                    
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-1">
                        Create Account
                    </h2>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                        Request access to the governance system
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label htmlFor="username" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Username
                        </label>
                        <input
                            id="username"
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-all"
                            placeholder="Choose a username"
                            required
                            autoComplete="username"
                            minLength={3}
                        />
                    </div>

                    <div>
                        <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Email Address
                        </label>
                        <input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-all"
                            placeholder="your.email@example.com"
                            required
                            autoComplete="email"
                        />
                    </div>

                    <div>
                        <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Password
                        </label>
                        <input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-all"
                            placeholder="Choose a password"
                            required
                            autoComplete="new-password"
                            minLength={8}
                        />
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            Minimum 8 characters
                        </p>
                    </div>

                    <div>
                        <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Confirm Password
                        </label>
                        <input
                            id="confirmPassword"
                            type="password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-all"
                            placeholder="Confirm your password"
                            required
                            autoComplete="new-password"
                            minLength={8}
                        />
                    </div>

                    {error && (
                        <div className="flex items-center gap-2 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-3 rounded-lg animate-in fade-in duration-300">
                            <AlertCircle className="w-4 h-4 flex-shrink-0" />
                            {error}
                        </div>
                    )}

                    <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
                        <p className="text-xs text-blue-800 dark:text-blue-300">
                            ℹ️ Your account will be pending until approved by an administrator.
                            You'll be able to login once approved.
                        </p>
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-all duration-200 hover:shadow-lg hover:scale-[1.02] active:scale-[0.98]"
                    >
                        {isLoading ? (
                            <>
                                <Loader2 className="w-4 h-4 animate-spin" />
                                Submitting Request...
                            </>
                        ) : (
                            'Create Account'
                        )}
                    </button>
                </form>

                <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-sm text-center text-gray-600 dark:text-gray-400">
                        Already have an account?{' '}
                        <Link to="/login" className="text-blue-600 dark:text-blue-400 hover:underline font-medium transition-colors">
                            Sign In
                        </Link>
                    </p>
                </div>

                <div className="mt-4">
                    <p className="text-xs text-center text-gray-500 dark:text-gray-400">
                        Intelligence requires governance
                    </p>
                </div>
            </div>
        </>
    );
}
