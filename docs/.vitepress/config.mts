import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'

export default withMermaid(
  defineConfig({
    title: 'uvr',
    description: 'Release management for uv workspaces',
    base: '/uvr/',
    srcExclude: ['adr/**'],
    head: [['link', { rel: 'icon', type: 'image/svg+xml', href: '/uvr/favicon.svg' }]],

    themeConfig: {
      nav: [
        {
          text: 'Guide',
          items: [
            { text: 'Getting Started', link: '/guide/getting-started' },
            { text: 'Releasing', link: '/guide/releasing' },
            { text: 'Versions', link: '/guide/versions' },
            { text: 'Configuration', link: '/guide/configuration' },
            { text: 'Release with Claude', link: '/guide/claude' },
            { text: 'Reference', link: '/guide/reference' },
          ],
        },
        {
          text: 'Internals',
          items: [
            { text: 'Architecture', link: '/internals/architecture' },
            { text: 'Change Detection', link: '/internals/change-detection' },
            { text: 'Release Pipeline', link: '/internals/pipeline' },
            { text: 'Build System', link: '/internals/build' },
          ],
        },
        { text: 'Changelog', link: '/CHANGELOG' },
      ],

      sidebar: {
        '/guide/': [
          {
            text: 'Guide',
            items: [
              { text: 'Getting Started', link: '/guide/getting-started' },
              { text: 'Releasing', link: '/guide/releasing' },
              { text: 'Versions', link: '/guide/versions' },
              { text: 'Configuration', link: '/guide/configuration' },
              { text: 'Release with Claude', link: '/guide/claude' },
              { text: 'Reference', link: '/guide/reference' },
            ],
          },
        ],
        '/internals/': [
          {
            text: 'Internals',
            items: [
              { text: 'Architecture', link: '/internals/architecture' },
              { text: 'Change Detection', link: '/internals/change-detection' },
              { text: 'Release Pipeline', link: '/internals/pipeline' },
              { text: 'Build System', link: '/internals/build' },
            ],
          },
        ],
      },

      socialLinks: [
        { icon: 'github', link: 'https://github.com/tylerpayne/uvr' },
      ],

      search: {
        provider: 'local',
      },

      editLink: {
        pattern: 'https://github.com/tylerpayne/uvr/edit/main/docs/:path',
      },
    },

    mermaid: {},
  })
)
