import React, { useState, useEffect } from 'react';
import { Shield, Users, Key, Plus, Edit, Trash2, Check, X, UserPlus, Lock, Unlock } from 'lucide-react';
import { User, UserRole, Permission, ROLE_TEMPLATES, hasPermission, canDelegatePermission, hasTierAccess } from '../types/auth';

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
    // TODO: Fetch from API
    // Mock data for demonstration
    const mockUsers: User[] = [
      {
        user_id: 'u001',
        username: 'maj.smith',
        email: 'smith.j@army.mil',
        rank: 'MAJ',
        position: 'Battalion XO',
        unit_id: 'bn-houston',
        role: ROLE_TEMPLATES.TIER_2_XO_MANAGER,
        created_at: '2025-01-15',
        is_active: true
      },
      {
        user_id: 'u002',
        username: 'sgt.jones',
        email: 'jones.m@army.mil',
        rank: 'SGT',
        position: '420T',
        unit_id: 'bn-houston',
        role: ROLE_TEMPLATES.TIER_3_420T_ADMIN,
        created_at: '2025-01-15',
        is_active: true
      }
    ];
    setUsers(mockUsers);
  };

  const createUser = async (userData: Partial<User>) => {
    // TODO: API call to create user
    console.log('Creating user:', userData);
    loadUsers();
    setShowCreateModal(false);
  };

  const updateUser = async (userId: string, updates: Partial<User>) => {
    // TODO: API call to update user
    console.log('Updating user:', userId, updates);
    loadUsers();
    setShowEditModal(false);
  };

  const delegatePermission = async (userId: string, permission: Permission, grant: boolean) => {
    if (!canDelegatePermission(currentUser, permission)) {
      alert('You do not have authority to delegate this permission');
      return;
    }
    
    // TODO: API call to update user permissions
    console.log(`${grant ? 'Granting' : 'Revoking'} permission ${permission} for user ${userId}`);
    loadUsers();
  };

  const deactivateUser = async (userId: string) => {
    // TODO: API call to deactivate user
    console.log('Deactivating user:', userId);
    loadUsers();
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
                      <Lock className="w-4 h-4 text-gray-400" title="Cannot delegate this permission" />
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

export default UserManagement;
