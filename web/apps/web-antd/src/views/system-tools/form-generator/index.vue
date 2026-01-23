<script lang="ts" setup>
import type FcDesigner from '@form-create/designer';

import { Page } from '@vben/common-ui';

import { computed, ref } from 'vue';

import { useWindowSize } from '@vueuse/core';

import { Button, message, Modal } from 'ant-design-vue';

const designerRef = ref<InstanceType<typeof FcDesigner>>();

// 让设计器在不同分辨率下尽量占满可用空间
const { height } = useWindowSize();
const designerHeight = computed(() => `${Math.max(height.value - 220, 600)}px`);

function handlePreview() {
  designerRef.value?.openPreview();
}

async function handleCopyJson() {
  const json = designerRef.value?.getJson?.() ?? '';
  if (!json) {
    message.warning('当前没有可导出的表单规则');
    return;
  }

  try {
    await navigator.clipboard.writeText(json);
    message.success('已复制表单规则 JSON');
  } catch {
    Modal.info({
      title: '表单规则 JSON',
      content: json,
      width: 900,
    });
  }
}

function handleClear() {
  Modal.confirm({
    title: '确认清空？',
    content: '清空后当前设计内容将被移除（不可撤销）。',
    okText: '确认',
    cancelText: '取消',
    onOk: () => {
      designerRef.value?.clearDragRule?.();
      message.success('已清空');
    },
  });
}
</script>

<template>
  <Page auto-content-height>
    <div class="mb-3 flex flex-wrap items-center gap-2">
      <Button type="primary" @click="handlePreview">预览</Button>
      <Button @click="handleCopyJson">复制 JSON</Button>
      <Button danger @click="handleClear">清空</Button>
    </div>

    <!-- FcDesigner 由 @form-create/designer 插件全局注册 -->
    <fc-designer ref="designerRef" :height="designerHeight" />
  </Page>
</template>

