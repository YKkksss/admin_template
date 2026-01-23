<script lang="ts" setup>
import type {
  OnActionClickParams,
  VxeTableGridOptions,
} from '#/adapter/vxe-table';
import type { SystemDictApi } from '#/api/system/dict';

import { computed } from 'vue';
import { useRoute } from 'vue-router';

import { Page, useVbenDrawer } from '@vben/common-ui';
import { Plus } from '@vben/icons';

import { Button, message, Modal } from 'ant-design-vue';

import { useVbenVxeGrid } from '#/adapter/vxe-table';
import { deleteDictData, getDictDataList } from '#/api/system/dict';
import PageBackHeader from '#/components/page-back-header/index.vue';
import { $t } from '#/locales';

import { useColumns, useGridFormSchema } from './data';
import Form from './modules/form.vue';

const route = useRoute();
const fixedTypeCode = computed(() => {
  const value = route.query.typeCode;
  return typeof value === 'string' && value.trim() ? value.trim() : undefined;
});
const dictDisplayName = computed(() => {
  const value = route.query.typeName;
  if (typeof value === 'string' && value.trim()) return value.trim();
  return fixedTypeCode.value || $t('system.dict.data.title');
});

const [FormDrawer, formDrawerApi] = useVbenDrawer({
  connectedComponent: Form,
  destroyOnClose: true,
});

const [Grid, gridApi] = useVbenVxeGrid({
  formOptions: {
    schema: useGridFormSchema(fixedTypeCode.value),
    submitOnChange: true,
  },
  gridOptions: {
    columns: useColumns(onActionClick),
    height: 'auto',
    keepSource: true,
    proxyConfig: {
      ajax: {
        query: async ({ page }, formValues) => {
          const typeCode = formValues?.typeCode || fixedTypeCode.value;
          if (!typeCode) {
            return { items: [], total: 0 };
          }
          return await getDictDataList({
            page: page.currentPage,
            pageSize: page.pageSize,
            ...formValues,
            typeCode,
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
  } as VxeTableGridOptions<SystemDictApi.DictData>,
});

function onRefresh() {
  gridApi.query();
}

function onEdit(row: SystemDictApi.DictData) {
  formDrawerApi.setData(row).open();
}

function onCreate() {
  const typeCode = fixedTypeCode.value;
  formDrawerApi.setData(typeCode ? ({ typeCode } as any) : null).open();
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

async function onDelete(row: SystemDictApi.DictData) {
  try {
    await confirm(
      $t('ui.actionMessage.deleteConfirm', [row.label]),
      $t('ui.actionTitle.delete', [$t('system.dict.data.title')]),
    );
  } catch {
    return;
  }

  deleteDictData(row.id)
    .then(() => {
      message.success({
        content: $t('ui.actionMessage.deleteSuccess', [row.label]),
      });
      onRefresh();
    })
    .catch(() => {
      // 错误提示由全局 request 拦截器处理
    });
}

function onActionClick(e: OnActionClickParams<SystemDictApi.DictData>) {
  switch (e.code) {
    case 'edit': {
      onEdit(e.row);
      break;
    }
    case 'delete': {
      onDelete(e.row);
      break;
    }
    default: {
      break;
    }
  }
}
</script>

<template>
  <Page auto-content-height>
    <PageBackHeader :fallback-path="'/system/dict'" :title="dictDisplayName" />
    <FormDrawer @success="onRefresh" />
    <Grid>
      <template #toolbar-actions>
        <Button type="primary" @click="onCreate">
          <Plus class="size-5" />
          {{ $t('ui.actionTitle.create', [$t('system.dict.data.title')]) }}
        </Button>
      </template>
    </Grid>
  </Page>
</template>
