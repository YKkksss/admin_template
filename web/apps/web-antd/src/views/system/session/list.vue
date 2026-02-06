<script lang="ts" setup>
import type { VxeTableGridOptions } from '#/adapter/vxe-table';
import type { SystemSessionApi } from '#/api/system/session';

import { Page } from '@vben/common-ui';
import { LogOut } from '@vben/icons';

import { Button, message, Modal } from 'ant-design-vue';

import { useVbenVxeGrid } from '#/adapter/vxe-table';
import { batchKickSessions, getSessionList, kickSession } from '#/api/system/session';
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
          return await getSessionList({
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
  } as VxeTableGridOptions<SystemSessionApi.Session>,
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

async function onKick(row: SystemSessionApi.Session) {
  if (!row?.id) return;
  try {
    await confirm(
      $t('system.session.kickConfirm', [row.username]),
      $t('system.session.kick'),
    );
  } catch {
    return;
  }

  kickSession(row.id)
    .then(() => {
      message.success($t('system.session.kickSuccess'));
      onRefresh();
    })
    .catch(() => {});
}

async function onBatchKick() {
  const records = gridApi.grid?.getCheckboxRecords?.() ?? [];
  if (!records.length) {
    message.warning($t('system.session.selectToKick'));
    return;
  }

  try {
    await confirm($t('system.session.batchKickConfirm'), $t('system.session.batchKick'));
  } catch {
    return;
  }

  const ids = records.map((r: any) => r.id).filter(Boolean);
  if (!ids.length) return;

  batchKickSessions(ids)
    .then(() => {
      message.success($t('system.session.kickSuccess'));
      try {
        gridApi.grid?.clearCheckboxRow?.();
      } catch {}
      onRefresh();
    })
    .catch(() => {});
}

function onActionClick({ code, row }: { code: string; row: any }) {
  if (code === 'kick') onKick(row);
}
</script>

<template>
  <Page auto-content-height>
    <Grid>
      <template #toolbar-actions>
        <Button danger type="primary" @click="onBatchKick">
          <LogOut class="mr-1 size-5" />
          {{ $t('system.session.batchKick') }}
        </Button>
      </template>
    </Grid>
  </Page>
</template>
