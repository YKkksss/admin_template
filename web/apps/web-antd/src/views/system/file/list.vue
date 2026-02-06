<script lang="ts" setup>
import type { VxeTableGridOptions } from '#/adapter/vxe-table';
import type { SystemFileApi } from '#/api/system/file';

import { Page } from '@vben/common-ui';
import { useAppConfig } from '@vben/hooks';
import { useAccessStore } from '@vben/stores';
import { Trash2, Upload as UploadIcon } from '@vben/icons';

import { Button, message, Modal, Upload } from 'ant-design-vue';

import { useVbenVxeGrid } from '#/adapter/vxe-table';
import {
  batchDeleteFiles,
  deleteFile,
  getFileList,
  uploadFile,
} from '#/api/system/file';
import { $t } from '#/locales';

import { useColumns, useGridFormSchema } from './data';

const accessStore = useAccessStore();
const { apiURL } = useAppConfig(import.meta.env, import.meta.env.PROD);

function joinUrl(base: string, path: string) {
  const b = base.endsWith('/') ? base.slice(0, -1) : base;
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${b}${p}`;
}

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
          return await getFileList({
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
  } as VxeTableGridOptions<SystemFileApi.SysFile>,
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

function formatAuthHeader(token: null | string) {
  return token ? `Bearer ${token}` : '';
}

async function fetchBlob(url: string) {
  const resp = await fetch(url, {
    headers: {
      Authorization: formatAuthHeader(accessStore.accessToken),
    },
  });
  if (!resp.ok) {
    const text = await resp.text();
    let msg = text || '请求失败';
    try {
      const json = JSON.parse(text || '{}');
      msg = json?.error || json?.message || msg;
    } catch {}
    throw new Error(msg);
  }
  const blob = await resp.blob();
  return blob;
}

async function onPreview(row: SystemFileApi.SysFile) {
  try {
    const blob = await fetchBlob(
      joinUrl(apiURL, `/system/file/${row.id}/preview`),
    );
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank');
    setTimeout(() => URL.revokeObjectURL(url), 60_000);
  } catch (err: any) {
    message.error(err?.message || $t('system.file.previewFailed'));
  }
}

async function onDownload(row: SystemFileApi.SysFile) {
  try {
    const blob = await fetchBlob(
      joinUrl(apiURL, `/system/file/${row.id}/download`),
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = row.originalName || 'download';
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  } catch (err: any) {
    message.error(err?.message || $t('system.file.downloadFailed'));
  }
}

async function onDelete(row: SystemFileApi.SysFile) {
  if (!row?.id) return;
  try {
    await confirm(
      $t('system.file.deleteConfirm', [row.originalName]),
      $t('common.delete'),
    );
  } catch {
    return;
  }

  deleteFile(row.id)
    .then(() => {
      message.success($t('system.file.deleteSuccess'));
      onRefresh();
    })
    .catch(() => {});
}

async function onBatchDelete() {
  const records = gridApi.grid?.getCheckboxRecords?.() ?? [];
  if (!records.length) {
    message.warning($t('system.file.selectToDelete'));
    return;
  }

  try {
    await confirm($t('system.file.batchDeleteConfirm'), $t('system.file.batchDelete'));
  } catch {
    return;
  }

  const ids = records.map((r: any) => r.id).filter(Boolean);
  if (!ids.length) return;

  batchDeleteFiles(ids)
    .then(() => {
      message.success($t('system.file.deleteSuccess'));
      try {
        gridApi.grid?.clearCheckboxRow?.();
      } catch {}
      onRefresh();
    })
    .catch(() => {});
}

async function onUpload(options: any) {
  const file = options?.file as File;
  if (!file) {
    options?.onError?.(new Error('文件不能为空'));
    return;
  }

  try {
    await uploadFile(file);
    message.success($t('system.file.uploadSuccess'));
    options?.onSuccess?.({}, file);
    onRefresh();
  } catch (err: any) {
    options?.onError?.(err);
    message.error(err?.message || '上传失败');
  }
}

function onActionClick({ code, row }: { code: string; row: any }) {
  if (code === 'preview') onPreview(row);
  if (code === 'download') onDownload(row);
  if (code === 'delete') onDelete(row);
}
</script>

<template>
  <Page auto-content-height>
    <Grid>
      <template #toolbar-actions>
        <Upload :custom-request="onUpload" :show-upload-list="false">
          <Button type="primary">
            <UploadIcon class="mr-1 size-5" />
            {{ $t('system.file.upload') }}
          </Button>
        </Upload>
        <Button danger type="primary" @click="onBatchDelete">
          <Trash2 class="mr-1 size-5" />
          {{ $t('system.file.batchDelete') }}
        </Button>
      </template>
    </Grid>
  </Page>
</template>
