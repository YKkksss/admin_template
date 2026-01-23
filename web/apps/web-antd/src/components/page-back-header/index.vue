<script lang="ts" setup>
import { computed } from 'vue';
import { useRouter } from 'vue-router';

import { IconifyIcon } from '@vben/icons';

import { Button } from 'ant-design-vue';

type Props = {
  /** 标题（通常为当前页面/当前对象名称） */
  title?: string;
  /** 返回按钮文字 */
  backText?: string;
  /** 没有可返回历史记录时的兜底跳转地址，避免跳出系统 */
  fallbackPath?: string;
  /** 返回图标（Iconify） */
  icon?: string;
};

const props = withDefaults(defineProps<Props>(), {
  backText: '返回',
  fallbackPath: '/',
  icon: 'lucide:arrow-left',
});

const router = useRouter();

const canGoBack = computed(() => {
  const state = window.history.state as any;
  return !!state && state.back != null;
});

async function handleBack() {
  // 优先返回到上一个路由；没有历史记录时回退到指定地址
  if (canGoBack.value) {
    router.back();
    return;
  }
  await router.push(props.fallbackPath);
}
</script>

<template>
  <div class="mb-3 flex items-center justify-between">
    <div class="flex min-w-0 items-center gap-2">
      <Button type="link" class="px-0" @click="handleBack">
        <IconifyIcon :icon="icon" class="mr-1 size-4" />
        {{ backText }}
      </Button>

      <template v-if="$slots.title || title">
        <div class="h-4 w-px bg-gray-200"></div>
        <div class="min-w-0 flex-1 text-base font-medium leading-6">
          <slot name="title">
            <span class="truncate">{{ title }}</span>
          </slot>
        </div>
      </template>
    </div>

    <div class="flex items-center gap-2">
      <slot name="extra"></slot>
    </div>
  </div>
</template>

