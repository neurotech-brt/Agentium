Created frontend so need to implement api for backend.


Authentication Endpoints
MethodEndpointDescriptionAuth RequiredPOST/api/v1/auth/signupUser signup requestNoPOST/api/v1/auth/loginUser loginNoPOST/api/v1/auth/verifyVerify JWT tokenNoPOST/api/v1/auth/change-passwordChange own passwordYes
Admin User Management Endpoints
MethodEndpointDescriptionAuth RequiredGET/api/v1/admin/users/pendingGet pending usersAdminGET/api/v1/admin/usersGet all approved usersAdminPOST/api/v1/admin/users/{id}/approveApprove userAdminPOST/api/v1/admin/users/{id}/rejectReject userAdminDELETE/api/v1/admin/users/{id}Delete userAdminPOST/api/v1/admin/users/{id}/change-passwordChange user passwordAdmin