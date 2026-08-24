export default defineNuxtRouteMiddleware(async (to) => {
  const auth = useAuthStore()
  if (!auth.isAuthenticated) {
    return navigateTo({ path: '/connexion', query: { redirect: to.fullPath } })
  }
  if (!auth.user) await auth.fetchMe()
  // fetchMe() clears the session on an invalid/expired token instead of
  // throwing — re-check here rather than falling into the role check below,
  // which would send an actually-logged-out user to /profil (itself gated,
  // so it eventually bounces to /connexion anyway, but via an extra hop that
  // loses this page as the post-login redirect target).
  if (!auth.isAuthenticated) {
    return navigateTo({ path: '/connexion', query: { redirect: to.fullPath } })
  }
  if (auth.user?.role !== 'vendor') {
    return navigateTo('/profil')
  }
  if (!auth.user.email_verified) {
    return navigateTo('/vendeur/verification-email')
  }
})
