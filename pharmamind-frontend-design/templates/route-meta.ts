import type { RouteRecordRaw } from 'vue-router'

export interface FrontendRouteMeta {
  title: string
  description?: string
  module?: string
  navLabel?: string
  navIcon?: string
  requiredPermissions?: string[]
  public?: boolean
  placeholder?: boolean
}

export type AppRouteRecord = RouteRecordRaw & {
  meta?: FrontendRouteMeta
}

export const appRoutes: AppRouteRecord[] = [
  {
    path: '/example',
    component: () => import('./ExampleView.vue'),
    meta: {
      title: '示例页面',
      description: '页面用途和当前工作范围。',
      module: 'admin',
      navLabel: '示例页面',
      navIcon: 'Document',
      requiredPermissions: ['example:read'],
    },
  },
]
