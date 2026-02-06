<script lang="ts" setup>
import type { VxeTableGridOptions } from '#/adapter/vxe-table';
import type { MonitorLogApi } from '#/api/monitor/log';

import { Page } from '@vben/common-ui';
import { Eraser, Trash2 } from '@vben/icons';

import { Button, message, Modal } from 'ant-design-vue';

import { useVbenVxeGrid } from '#/adapter/vxe-table';
import {
  batchDeleteOperationLogs,
  clearOperationLogs,
  deleteOperationLog,
  getOperationLogList,
} from '#/api/monitor/log';
import { $t } from '#/locales';

import { useColumns, useGridFormSchema } from './data';

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
          return await getOperationLogList({
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
  } as VxeTableGridOptions<MonitorLogApi.OperationLog>,
});

function onRefresh() {
  gridApi.query();
}

function confirm(content: string, title: string) {
  return new Promise((resolve, reject) => {
    Modal.confirm({
      content,
      onCancel() {
        reject(new Error('已取消'));
      },
      onOk() {
        resolve(true);
      },
      title,
    });
  });
}

function onActionClick({ code, row }: { code: string; row: any }) {
  if (code === 'delete') {
    onDelete(row);
  }
}

function onDelete(row: MonitorLogApi.OperationLog) {
  deleteOperationLog(row.id)
    .then(() => {
      message.success($t('ui.actionMessage.deleteSuccess', [row.id]));
      onRefresh();
    })
    .catch(() => {});
}

async function onBatchDelete() {
  const records = gridApi.grid?.getCheckboxRecords?.() ?? [];
  if (!records.length) {
    message.warning($t('monitor.selectToDelete'));
    return;
  }
  try {
    await confirm($t('monitor.batchDeleteConfirm'), $t('monitor.batchDelete'));
  } catch {
    return;
  }
  const ids = records.map((r: any) => r.id).filter(Boolean);
  if (!ids.length) return;
  batchDeleteOperationLogs(ids)
    .then(() => {
      message.success($t('ui.actionMessage.deleteSuccess', [$t('monitor.name')]));
      try {
        gridApi.grid?.clearCheckboxRow?.();
      } catch {}
      onRefresh();
    })
    .catch(() => {});
}

async function onClear() {
  try {
    await confirm($t('monitor.clearConfirm'), $t('monitor.clear'));
  } catch {
    return;
  }
  clearOperationLogs()
    .then(() => {
      message.success($t('monitor.clearSuccess'));
      onRefresh();
    })
    .catch(() => {});
}
</script>

<template>
  <Page auto-content-height>
    <Grid>
      <template #toolbar-actions>
        <Button danger type="primary" @click="onBatchDelete">
          <Trash2 class="mr-1 size-5" />
          {{ $t('monitor.batchDelete') }}
        </Button>
        <Button danger @click="onClear">
          <Eraser class="mr-1 size-5" />
          {{ $t('monitor.clear') }}
        </Button>
      </template>
    </Grid>
  </Page>
</template>
