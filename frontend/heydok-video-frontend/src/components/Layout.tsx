import React from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  HomeIcon, 
  VideoCameraIcon, 
  CalendarIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon 
} from '@heroicons/react/24/outline';

const Layout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 w-64 bg-white shadow-lg">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="px-6 py-4 border-b border-gray-200">
            <h1 className="text-2xl font-bold text-heydok-primary">heydok</h1>
            <p className="text-sm text-gray-500 mt-1">Video Conferencing</p>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            <Link
              to="/dashboard"
              className="flex items-center px-4 py-2 text-gray-700 rounded-lg hover:bg-heydok-light hover:text-heydok-primary transition-colors"
            >
              <HomeIcon className="w-5 h-5 mr-3" />
              Dashboard
            </Link>
            
            <Link
              to="/rooms"
              className="flex items-center px-4 py-2 text-gray-700 rounded-lg hover:bg-heydok-light hover:text-heydok-primary transition-colors"
            >
              <VideoCameraIcon className="w-5 h-5 mr-3" />
              Räume
            </Link>

            <Link
              to="/schedule"
              className="flex items-center px-4 py-2 text-gray-700 rounded-lg hover:bg-heydok-light hover:text-heydok-primary transition-colors"
            >
              <CalendarIcon className="w-5 h-5 mr-3" />
              Terminplanung
            </Link>

            <Link
              to="/settings"
              className="flex items-center px-4 py-2 text-gray-700 rounded-lg hover:bg-heydok-light hover:text-heydok-primary transition-colors"
            >
              <Cog6ToothIcon className="w-5 h-5 mr-3" />
              Einstellungen
            </Link>
          </nav>

          {/* User Info & Logout */}
          <div className="border-t border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900">{user?.email}</p>
                <p className="text-xs text-gray-500">{user?.role}</p>
              </div>
              <button
                onClick={handleLogout}
                className="p-2 text-gray-500 hover:text-red-600 transition-colors"
                title="Abmelden"
              >
                <ArrowRightOnRectangleIcon className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="ml-64">
        <main className="p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout; 