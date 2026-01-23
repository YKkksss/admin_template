<script lang="ts" setup>
import { computed, ref } from 'vue';

import { useVbenDrawer } from '@vben/common-ui';

import { Descriptions, Spin } from 'ant-design-vue';

import {
  getInboxNoticeDetailApi,
  markInboxNoticeReadApi,
  type NoticeApi,
} from '#/api';
import { $t } from '#/locales';

const emits = defineEmits(['success']);

const detail = ref<NoticeApi.InboxItem | null>(null);
const loading = ref(false);

const [Drawer, drawerApi] = useVbenDrawer({
  footer: false,
  destroyOnClose: true,
  async onOpenChange(isOpen) {
    if (!isOpen) return;

    const row = drawerApi.getData<NoticeApi.InboxItem>();
    if (!row?.id) return;

    loading.value = true;
    try {
      const data = await getInboxNoticeDetailApi(row.id);
      detail.value = data;

      // 打开详情视为已读（只对当前用户生效）
      if (data && data.isRead === false) {
        await markInboxNoticeReadApi(row.id);
        if (detail.value) {
          detail.value.isRead = true;
        }
        emits('success');
      }
    } finally {
      loading.value = false;
    }
  },
});

const typeText = computed(() => {
  const t = detail.value?.type;
  if (t === 1) return $t('notice.typeText.1');
  if (t === 2) return $t('notice.typeText.2');
  if (t === 3) return $t('notice.typeText.3');
  return '-';
});
</script>

<template>
  <Drawer :title="$t('notice.detail')">
    <Spin :spinning="loading">
      <Descriptions v-if="detail" bordered :column="1" size="small">
        <Descriptions.Item :label="$t('notice.messageTitle')">
          {{ detail.title }}
        </Descriptions.Item>
        <Descriptions.Item :label="$t('notice.type')">
          {{ typeText }}
        </Descriptions.Item>
        <Descriptions.Item :label="$t('notice.createTime')">
          {{ detail.createTime }}
        </Descriptions.Item>
        <Descriptions.Item :label="$t('notice.summary')">
          {{ detail.message }}
        </Descriptions.Item>
        <Descriptions.Item :label="$t('notice.content')">
          <div class="whitespace-pre-wrap break-words">
            {{ detail.content ?? '' }}
          </div>
        </Descriptions.Item>
      </Descriptions>
    </Spin>
  </Drawer>
</template>
