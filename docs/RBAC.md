**RBAC**
- **Purpose**: centralize permission keys, role templates, and route mappings used by TAAIP.

**Permission Keys (canonical)**
- app.read: baseline read access (auto-granted)
- app.export: baseline export capability (auto-granted)
- datahub.view
- datahub.upload_raw
- datahub.manage_registry
- datahub.view_runs
- commandcenter.view
- marketintel.view
- operations.view
- roi.view
- roi.view_detail
- planning.view
- planning.edit
- events.view
- events.edit
- assets.view
- assets.edit
- schools.view
- schools.edit
- budget.view
- budget.edit
- helpdesk.view
- helpdesk.submit
- helpdesk.manage
- admin.view
- admin.users.manage
- admin.roles.manage
- admin.audit.view

**Roles (templates)**
- ADMIN: all permissions
- 420T_FULL: all non-admin permissions + datahub.upload_raw
- COMMAND_READONLY: view + export only
- STAFF_PLANNER: planning/events/assets edit; rest view
- STAFF_ANALYST: analytics/roi view + export
- USER: baseline read + export only

**How it works**
- Backend seeds `permission`, `role_template`, and `role_template_permission` tables at startup (see `services/api/app/db.py`).
- Admin endpoints under `/api/v2/admin` allow assigning role templates and per-user permission overrides.
- The frontend loads `/api/me` (and `/api/auth/me`) to fetch effective permissions and roles. The `AuthContext` exposes `permissions` map.
- Routes are mapped to permission keys in `apps/web/src/rbac/routePerms.ts`. The sidebar filters nav items using those mappings.
- Use `apps/web/src/components/ProtectedRoute.tsx` to guard React routes by required permissions.

**Adding a new route permission**
1. Add the permission key to `services/api/app/db.py` seed block.
2. If desired, add the permission to a role template by inserting into `role_template_permission`.
3. Add a mapping in `apps/web/src/rbac/routePerms.ts` for the route.
4. Protect backend endpoints by requiring permission via `from .routers.rbac import require_perm` and adding `Depends(require_perm('permission.key'))`.
