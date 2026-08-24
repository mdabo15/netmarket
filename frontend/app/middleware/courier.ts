export default defineNuxtRouteMiddleware(async (to) => {
  const auth = useAuthStore()
  if (!auth.isAuthenticated) {
    return navigateTo({ path: '/connexion', query: { redirect: to.fullPath } })
  }
  if (!auth.user) await auth.fetchMe()
  if (!auth.isAuthenticated) {
    return navigateTo({ path: '/connexion', query: { redirect: to.fullPath } })
  }
  if (auth.user?.role !== 'courier') {
    return navigateTo('/profil')
  }
})
