<script lang="ts" setup>
import type { OnActionClickParams, VxeTableGridOptions } from '#/adapter/vxe-table';
import type { NoticeApi } from '#/api';

import { Page, useVbenDrawer } from '@vben/common-ui';
import { Check, MailCheck, Trash2 } from '@vben/icons';

import { Button, message, Modal } from 'ant-design-vue';

import { useVbenVxeGrid } from '#/adapter/vxe-table';
import {
  deleteInboxNoticeApi,
  deleteInboxNoticeBatchApi,
  getInboxNoticesApi,
  markInboxNoticeReadAllApi,
  markInboxNoticeReadBatchApi,
} from '#/api';
import { useNoticeStore } from '#/store';
import { $t } from '#/locales';

import { useColumns, useGridFormSchema } from './data';
import Detail from './modules/detail.vue';

const noticeStore = useNoticeStore();

const [DetailDrawer, detailDrawerApi] = useVbenDrawer({
  connectedComponent: Detail,
  destroyOnClose: true,
});

const [Grid, gridApi] = useVbenVxeGrid({
  formOptions: {
    schema: useGridFormSchema(),
    submitOnChange: true,
  },
  gridOptions: {
    checkboxConfig: {
      highlight: true,
    },
    columns: useColumns(onActionClick),
    height: 'auto',
    keepSource: true,
    proxyConfig: {
      ajax: {
        query: async ({ page }, formValues) => {
          return await getInboxNoticesApi({
            page: page.currentPage,
            pageSize: page.pageSize,
            ...formValues,
          });
        },
      },
    },
    rowConfig: {
      keyField: 'id',
    },
    toolbarConfig: {
      custom: true,
      export: false,
      refresh: true,
      search: true,
      zoom: true,
    },
  } as VxeTableGridOptions<NoticeApi.InboxItem>,
});

function onRefresh() {
  gridApi.query();
  // 同步刷新铃铛未读列表
  noticeStore.refreshBellNotices();
}

function onActionClick(e: OnActionClickParams<NoticeApi.InboxItem>) {
  switch (e.code) {
    case 'delete': {
      onDelete(e.row);
      break;
    }
    case 'detail': {
      onDetail(e.row);
      break;
    }
    default: {
      break;
    }
  }
}

function onDetail(row: NoticeApi.InboxItem) {
  detailDrawerApi.setData(row).open();
}

function onDelete(row: NoticeApi.InboxItem) {
  deleteInboxNoticeApi(row.id)
    .then(() => {
      message.success($t('ui.actionMessage.deleteSuccess', [row.title]));
      onRefresh();
    })
    .catch(() => {
      // 错误提示由全局 request 拦截器处理
    });
}

/**
 * 将 Antd 的 Modal.confirm 封装为 Promise，方便在异步函数中调用
 */
function confirm(content: string, title: string) {
  return new Promise((reslove, reject) => {
    Modal.confirm({
      content,
      onCancel() {
        reject(new Error('已取消'));
      },
      onOk() {
        reslove(true);
      },
      title,
    });
  });
}

async function onBatchDelete() {
  const records = gridApi.grid?.getCheckboxRecords?.() ?? [];
  if (!records.length) {
    message.warning($t('notice.selectToDelete'));
    return;
  }

  try {
    await confirm($t('notice.batchDeleteConfirm'), $t('notice.batchDelete'));
  } catch {
    return;
  }

  const ids = records.map((r: any) => r.id).filter(Boolean);
  if (!ids.length) return;

  try {
    await deleteInboxNoticeBatchApi(ids);
    message.success($t('ui.actionMessage.deleteSuccess', [$t('notice.name')]));
    try {
      gridApi.grid?.clearCheckboxRow?.();
    } catch {
      // ignore
    }
    onRefresh();
  } catch {
    // 错误提示由全局 request 拦截器处理
  }
}

async function onBatchRead() {
  const records = gridApi.grid?.getCheckboxRecords?.() ?? [];
  if (!records.length) {
    message.warning($t('notice.selectToRead'));
    return;
  }

  const ids = records
    .filter((r: any) => r && r.id && r.isRead === false)
    .map((r: any) => r.id);

  if (!ids.length) {
    message.warning($t('notice.selectToRead'));
    return;
  }

  try {
    await confirm($t('notice.batchReadConfirm'), $t('notice.batchRead'));
  } catch {
    return;
  }

  try {
    await markInboxNoticeReadBatchApi(ids);
    message.success($t('notice.readSuccess'));
    try {
      gridApi.grid?.clearCheckboxRow?.();
    } catch {
      // ignore
    }
    onRefresh();
  } catch {
    // 错误提示由全局 request 拦截器处理
  }
}

async function onReadAll() {
  try {
    await confirm($t('notice.readAllConfirm'), $t('notice.readAll'));
  } catch {
    return;
  }

  try {
    await markInboxNoticeReadAllApi();
    message.success($t('notice.readSuccess'));
    onRefresh();
  } catch {
    // 错误提示由全局 request 拦截器处理
  }
}
</script>

<template>
  <Page auto-content-height>
    <DetailDrawer @success="onRefresh" />
    <Grid>
      <template #toolbar-actions>
        <span class="mr-3 text-sm text-muted-foreground">
          {{ $t('notice.unreadCount', [noticeStore.unreadCount]) }}
        </span>
        <Button type="primary" @click="onReadAll">
          <MailCheck class="mr-1 size-5" />
          {{ $t('notice.readAll') }}
        </Button>
        <Button type="primary" @click="onBatchRead">
          <Check class="mr-1 size-5" />
          {{ $t('notice.batchRead') }}
        </Button>
        <Button danger type="primary" @click="onBatchDelete">
          <Trash2 class="mr-1 size-5" />
          {{ $t('notice.batchDelete') }}
        </Button>
      </template>
    </Grid>
  </Page>
</template>
