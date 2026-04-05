---
layout: page
---

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vitepress'

onMounted(() => {
  useRouter().go('/user-guide/01-getting-started')
})
</script>

Redirecting to [Getting Started](01-getting-started.md)...
