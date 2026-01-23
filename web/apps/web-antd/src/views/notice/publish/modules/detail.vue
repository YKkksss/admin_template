<script lang="ts" setup>
import { computed, ref } from 'vue';

import { useVbenDrawer } from '@vben/common-ui';

import { Descriptions, Spin } from 'ant-design-vue';

import { getOutboxNoticeDetailApi, type NoticeApi } from '#/api';
import { $t } from '#/locales';

const detail = ref<NoticeApi.OutboxDetail | null>(null);
const loading = ref(false);

const [Drawer, drawerApi] = useVbenDrawer({
  footer: false,
  destroyOnClose: true,
  async onOpenChange(isOpen) {
    if (!isOpen) return;

    const row = drawerApi.getData<NoticeApi.OutboxItem>();
    if (!row?.id) return;

    loading.value = true;
    try {
      detail.value = await getOutboxNoticeDetailApi(row.id);
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

const scopeText = computed(() => {
  const scope = detail.value?.sendScope;
  if (scope === 'all') return $t('notice.publish.sendScopeText.all');
  if (scope === 'dept') return $t('notice.publish.sendScopeText.dept');
  if (scope === 'user') return $t('notice.publish.sendScopeText.user');
  if (scope === 'mixed') return $t('notice.publish.sendScopeText.mixed');
  return $t('notice.publish.sendScopeText.unknown');
});
</script>

<template>
  <Drawer :title="$t('notice.publish.detail')">
    <Spin :spinning="loading">
      <Descriptions v-if="detail" bordered :column="1" size="small">
        <Descriptions.Item :label="$t('notice.messageTitle')">
          {{ detail.title }}
        </Descriptions.Item>
        <Descriptions.Item :label="$t('notice.type')">
          {{ typeText }}
        </Descriptions.Item>
        <Descriptions.Item :label="$t('notice.publish.sendScope')">
          {{ scopeText }}
        </Descriptions.Item>
        <Descriptions.Item :label="$t('notice.publish.receiverCount')">
          {{ detail.receiverCount }}
        </Descriptions.Item>
        <Descriptions.Item :label="$t('notice.createTime')">
          {{ detail.createTime }}
        </Descriptions.Item>
        <Descriptions.Item
          v-if="detail.deptNames && detail.deptNames.length > 0"
          :label="$t('notice.publish.deptIds')"
        >
          {{ detail.deptNames.join(', ') }}
        </Descriptions.Item>
        <Descriptions.Item
          v-if="detail.userNames && detail.userNames.length > 0"
          :label="$t('notice.publish.userIds')"
        >
          {{ detail.userNames.join(', ') }}
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
