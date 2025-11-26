import React, { useState, useEffect } from 'react';
import { Shield, Users, Key, Plus, Edit, Trash2, Check, X, UserPlus, Lock, Unlock } from 'lucide-react';
import { User, UserRole, Permission, ROLE_TEMPLATES, hasPermission, canDelegatePermission, hasTierAccess } from '../types/auth';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000';

// Helper function to convert tier string to number
const getTierNumber = (tier?: string): number => {
  if (!tier) return 3;
  if (tier.includes('4')) return 1;
  if (tier.includes('3')) return 2;
  if (tier.includes('2')) return 2;
  if (tier.includes('1')) return 3;
  return 3;
};

interface UserManagementProps {
  currentUser: User; // The logged-in user (should be Tier 3 or Tier 4)
}

export const UserManagement: React.FC<UserManagementProps> = ({ currentUser }) => {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showPermissionsModal, setShowPermissionsModal] = useState(false);
  
  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v2/users`);
      const data = await response.json();
      if (data.status === 'ok') {
        // Transform backend data to match frontend User type
        const transformedUsers: User[] = data.users.map((u: any) => ({
          user_id: u.id.toString(),
          username: u.username,
          email: u.email,
          rank: u.rank || '',
          position: u.position || '',
          unit_id: u.unit_id || '',
          role: {
            role_id: u.role || 'analyst',
            role_name: u.role || 'Analyst',
            tier: u.tier || 'tier-1-user',
            permissions: u.permissions || [],
            description: `${u.role} role`
          },
          created_at: u.created_at,
          is_active: u.is_active === 1 || u.is_active === true,
          last_login: u.last_login
        }));
        setUsers(transformedUsers);
      }
    } catch (error) {
      console.error('Error loading users:', error);
    }
  };

  const createUser = async (userData: Partial<User>) => {
    try {
      const response = await fetch(`${API_BASE}/api/v2/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: userData.username,
          email: userData.email,
          password: 'changeme123', // Default password
          rank: userData.rank,
          role: userData.role?.role_name || 'analyst',
          tier: getTierNumber(userData.role?.tier),
          permissions: userData.role?.permissions || []
        })
      });
      const data = await response.json();
      if (data.status === 'ok') {
        loadUsers();
        setShowCreateModal(false);
      }
    } catch (error) {
      console.error('Error creating user:', error);
    }
  };

  const updateUser = async (userId: string, updates: Partial<User>) => {
    try {
      const response = await fetch(`${API_BASE}/api/v2/users/${userId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: updates.email,
          rank: updates.rank,
          role: updates.role?.role_name,
          tier: getTierNumber(updates.role?.tier),
          is_active: updates.is_active
        })
      });
      const data = await response.json();
      if (data.status === 'ok') {
        loadUsers();
      }
    } catch (error) {
      console.error('Error updating user:', error);
    }
    setShowEditModal(false);
  };

  const delegatePermission = async (userId: string, permission: Permission, grant: boolean) => {
    if (!canDelegatePermission(currentUser, permission)) {
      alert('You do not have authority to delegate this permission');
      return;
    }
    
    try {
      const response = await fetch(`${API_BASE}/api/v2/users/${userId}/permissions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          permissions: [permission],
          action: grant ? 'grant' : 'revoke'
        })
      });
      const data = await response.json();
      if (data.status === 'ok') {
        loadUsers();
      }
    } catch (error) {
      console.error('Error managing permissions:', error);
    }
  };

  const deactivateUser = async (userId: string) => {
    if (!hasPermission(currentUser, 'manage_users')) {
      alert('You do not have permission to deactivate users');
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/api/v2/users/${userId}/deactivate`, {
        method: 'POST'
      });
      const data = await response.json();
      if (data.status === 'ok') {
        loadUsers();
      }
    } catch (error) {
      console.error('Error deactivating user:', error);
    }
  };

  // Check if current user can manage users
  if (!hasPermission(currentUser, 'manage_users')) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Lock className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <p className="text-xl font-bold text-gray-900">Access Denied</p>
          <p className="text-gray-600">You do not have permission to manage users</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-xl shadow-lg p-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <Users className="w-8 h-8" />
              User Management
            </h1>
            <p className="text-blue-100 mt-2">
              Your Access Level: <span className="font-bold">{currentUser.role.role_name}</span> ({currentUser.role.tier})
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-white text-blue-600 px-6 py-3 rounded-lg font-bold hover:bg-blue-50 flex items-center gap-2"
          >
            <UserPlus className="w-5 h-5" />
            Create User
          </button>
        </div>
      </div>

      {/* Current User Info */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
          <Shield className="w-6 h-6 text-yellow-500" />
          Your Administrative Capabilities
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="font-bold text-green-900">Can Manage Users</p>
            <p className="text-sm text-green-700">{hasPermission(currentUser, 'manage_users') ? 'Yes' : 'No'}</p>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="font-bold text-blue-900">Can Assign Roles</p>
            <p className="text-sm text-blue-700">{hasPermission(currentUser, 'assign_roles') ? 'Yes' : 'No'}</p>
          </div>
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <p className="font-bold text-purple-900">Can Delegate Permissions</p>
            <p className="text-sm text-purple-700">{hasPermission(currentUser, 'delegate_permissions') ? 'Yes' : 'No'}</p>
          </div>
        </div>
      </div>

      {/* User List */}
      <div className="bg-white rounded-xl shadow-md overflow-hidden">
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">System Users</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase">User</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase">Position</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase">Role / Tier</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {users.map(user => (
                <tr key={user.user_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div>
                      <p className="font-bold text-gray-900">{user.rank} {user.username}</p>
                      <p className="text-sm text-gray-600">{user.email}</p>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <p className="text-gray-900">{user.position}</p>
                    <p className="text-sm text-gray-600">{user.unit_id}</p>
                  </td>
                  <td className="px-6 py-4">
                    <div>
                      <p className="font-bold text-gray-900">{user.role.role_name}</p>
                      <span className={`inline-block px-2 py-1 rounded text-xs font-bold ${
                        user.role.tier === 'tier-4-global' ? 'bg-red-100 text-red-800' :
                        user.role.tier === 'tier-3-admin' ? 'bg-purple-100 text-purple-800' :
                        user.role.tier === 'tier-2-manager' ? 'bg-blue-100 text-blue-800' :
                        user.role.tier === 'tier-1-user' ? 'bg-green-100 text-green-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {user.role.tier.toUpperCase()}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {user.is_active ? (
                      <span className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-bold">
                        <Check className="w-3 h-3" /> Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-3 py-1 bg-red-100 text-red-800 rounded-full text-xs font-bold">
                        <X className="w-3 h-3" /> Inactive
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      <button
                        onClick={() => {
                          setSelectedUser(user);
                          setShowEditModal(true);
                        }}
                        className="p-2 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                        title="Edit User"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => {
                          setSelectedUser(user);
                          setShowPermissionsModal(true);
                        }}
                        className="p-2 bg-purple-100 text-purple-700 rounded hover:bg-purple-200"
                        title="Manage Permissions"
                      >
                        <Key className="w-4 h-4" />
                      </button>
                      {user.user_id !== currentUser.user_id && (
                        <button
                          onClick={() => {
                            if (confirm(`Deactivate user ${user.username}?`)) {
                              deactivateUser(user.user_id);
                            }
                          }}
                          className="p-2 bg-red-100 text-red-700 rounded hover:bg-red-200"
                          title="Deactivate User"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Permission Delegation Modal */}
      {showPermissionsModal && selectedUser && (
        <PermissionDelegationModal
          user={selectedUser}
          currentUser={currentUser}
          onDelegate={delegatePermission}
          onClose={() => {
            setShowPermissionsModal(false);
            setSelectedUser(null);
          }}
        />
      )}
    </div>
  );
};

// Permission Delegation Modal Component
const PermissionDelegationModal: React.FC<{
  user: User;
  currentUser: User;
  onDelegate: (userId: string, permission: Permission, grant: boolean) => void;
  onClose: () => void;
}> = ({ user, currentUser, onDelegate, onClose }) => {
  const allPermissions: Permission[] = [
    'view_all_dashboards',
    'view_analytics',
    'upload_data',
    'edit_data',
    'delete_data',
    'export_data',
    'create_events',
    'approve_events',
    'edit_events',
    'delete_events',
    'manage_twg',
    'manage_tdb',
    'assign_roles',
    'manage_users',
    'delegate_permissions',
    'edit_budget',
    'approve_budget',
    'system_admin'
  ];

  const hasUserPermission = (perm: Permission) => {
    return user.role.permissions.includes(perm) || user.custom_permissions?.includes(perm);
  };

  const canDelegate = (perm: Permission) => {
    return canDelegatePermission(currentUser, perm);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
        <div className="bg-gradient-to-r from-purple-600 to-indigo-700 px-6 py-4">
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Key className="w-6 h-6" />
            Manage Permissions: {user.username}
          </h2>
          <p className="text-purple-100 text-sm mt-1">
            Base Role: {user.role.role_name} ({user.role.tier})
          </p>
        </div>
        
        <div className="p-6 overflow-y-auto max-h-96">
          <div className="space-y-3">
            {allPermissions.map(permission => {
              const userHas = hasUserPermission(permission);
              const canDel = canDelegate(permission);
              const isRolePermission = user.role.permissions.includes(permission);
              
              return (
                <div key={permission} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50">
                  <div className="flex-1">
                    <p className="font-bold text-gray-900">{permission.replace(/_/g, ' ').toUpperCase()}</p>
                    {isRolePermission && (
                      <p className="text-xs text-blue-600">Included in base role</p>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-3">
                    {userHas ? (
                      <span className="flex items-center gap-1 text-green-700">
                        <Check className="w-4 h-4" /> Granted
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-gray-400">
                        <X className="w-4 h-4" /> Not Granted
                      </span>
                    )}
                    
                    {canDel && !isRolePermission && (
                      <button
                        onClick={() => onDelegate(user.user_id, permission, !userHas)}
                        className={`px-3 py-1 rounded font-bold text-sm ${
                          userHas
                            ? 'bg-red-100 text-red-700 hover:bg-red-200'
                            : 'bg-green-100 text-green-700 hover:bg-green-200'
                        }`}
                      >
                        {userHas ? 'Revoke' : 'Grant'}
                      </button>
                    )}
                    
                    {!canDel && (
                      <div title="Cannot delegate this permission">
                        <Lock className="w-4 h-4 text-gray-400" />
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        
        <div className="bg-gray-50 px-6 py-4 flex justify-end">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-gray-600 text-white rounded-lg font-bold hover:bg-gray-700"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

      {/* Create User Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white px-6 py-4">
              <h2 className="text-2xl font-bold flex items-center gap-2">
                <UserPlus className="w-6 h-6" />
                Create New User
              </h2>
            </div>
            <form onSubmit={(e) => {
              e.preventDefault();
              const formData = new FormData(e.currentTarget);
              createUser({
                username: formData.get('username') as string,
                email: formData.get('email') as string,
                rank: formData.get('rank') as string,
                role: {
                  role_id: formData.get('role') as string,
                  role_name: formData.get('role') as string,
                  tier: formData.get('tier') as AccessTier,
                  permissions: [],
                  description: ''
                }
              });
            }} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-1">Username</label>
                <input
                  type="text"
                  name="username"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  name="email"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-1">Rank</label>
                <input
                  type="text"
                  name="rank"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-1">Role</label>
                <select
                  name="role"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="analyst">Analyst</option>
                  <option value="recruiter">Recruiter</option>
                  <option value="station_commander">Station Commander</option>
                  <option value="company_commander">Company Commander</option>
                  <option value="420t">420T Administrator</option>
                  <option value="admin">Global Administrator</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-1">Tier</label>
                <select
                  name="tier"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="tier-1-user">Tier 1 - User</option>
                  <option value="tier-2-manager">Tier 2 - Manager</option>
                  <option value="tier-3-admin">Tier 3 - Administrator</option>
                  <option value="tier-4-global">Tier 4 - Global</option>
                </select>
              </div>
              <div className="flex gap-3 justify-end pt-4 border-t">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-6 py-2 bg-gray-300 text-gray-700 rounded-lg font-bold hover:bg-gray-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700"
                >
                  Create User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {showEditModal && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl">
            <div className="bg-gradient-to-r from-purple-600 to-indigo-700 text-white px-6 py-4">
              <h2 className="text-2xl font-bold flex items-center gap-2">
                <Edit className="w-6 h-6" />
                Edit User: {selectedUser.username}
              </h2>
            </div>
            <form onSubmit={(e) => {
              e.preventDefault();
              const formData = new FormData(e.currentTarget);
              updateUser(selectedUser.user_id, {
                email: formData.get('email') as string,
                rank: formData.get('rank') as string,
                is_active: formData.get('is_active') === 'true'
              });
            }} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  name="email"
                  defaultValue={selectedUser.email}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-1">Rank</label>
                <input
                  type="text"
                  name="rank"
                  defaultValue={selectedUser.rank}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-1">Status</label>
                <select
                  name="is_active"
                  defaultValue={selectedUser.is_active ? 'true' : 'false'}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="true">Active</option>
                  <option value="false">Inactive</option>
                </select>
              </div>
              <div className="flex gap-3 justify-end pt-4 border-t">
                <button
                  type="button"
                  onClick={() => {
                    setShowEditModal(false);
                    setSelectedUser(null);
                  }}
                  className="px-6 py-2 bg-gray-300 text-gray-700 rounded-lg font-bold hover:bg-gray-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-6 py-2 bg-purple-600 text-white rounded-lg font-bold hover:bg-purple-700"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Permissions Management Modal */}
      {showPermissionsModal && selectedUser && (
        <PermissionsModal
          user={selectedUser}
          currentUser={currentUser}
          onDelegate={delegatePermission}
          onClose={() => {
            setShowPermissionsModal(false);
            setSelectedUser(null);
          }}
        />
      )}
    </div>
  );
};

export default UserManagement;
