import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, VxeTableGridOptions } from '#/adapter/vxe-table';
import type { NoticeApi } from '#/api';

import { $t } from '#/locales';

export function useGridFormSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'keyword',
      label: $t('notice.keyword'),
    },
    {
      component: 'Select',
      componentProps: {
        allowClear: true,
        options: [
          { label: $t('notice.typeText.1'), value: 1 },
          { label: $t('notice.typeText.2'), value: 2 },
          { label: $t('notice.typeText.3'), value: 3 },
        ],
      },
      fieldName: 'type',
      label: $t('notice.type'),
    },
  ];
}

export function useColumns<T = NoticeApi.OutboxItem>(
  onActionClick: OnActionClickFn<T>,
): VxeTableGridOptions['columns'] {
  return [
    {
      field: 'title',
      title: $t('notice.messageTitle'),
      minWidth: 200,
    },
    {
      field: 'message',
      title: $t('notice.summary'),
      minWidth: 260,
      showOverflow: 'tooltip',
    },
    {
      field: 'type',
      title: $t('notice.type'),
      width: 100,
      cellRender: {
        name: 'CellTag',
        options: [
          { color: 'success', label: $t('notice.typeText.1'), value: 1 },
          { color: 'processing', label: $t('notice.typeText.2'), value: 2 },
          { color: 'error', label: $t('notice.typeText.3'), value: 3 },
        ],
      },
    },
    {
      field: 'sendScope',
      title: $t('notice.publish.sendScope'),
      width: 140,
      cellRender: {
        name: 'CellTag',
        options: [
          {
            color: 'success',
            label: $t('notice.publish.sendScopeText.all'),
            value: 'all',
          },
          {
            color: 'processing',
            label: $t('notice.publish.sendScopeText.dept'),
            value: 'dept',
          },
          {
            color: 'warning',
            label: $t('notice.publish.sendScopeText.user'),
            value: 'user',
          },
          {
            color: 'warning',
            label: $t('notice.publish.sendScopeText.mixed'),
            value: 'mixed',
          },
          {
            color: 'default',
            label: $t('notice.publish.sendScopeText.unknown'),
            value: 'unknown',
          },
        ],
      },
    },
    {
      field: 'receiverCount',
      title: $t('notice.publish.receiverCount'),
      width: 120,
    },
    {
      field: 'createTime',
      title: $t('notice.createTime'),
      width: 200,
    },
    {
      align: 'center',
      cellRender: {
        attrs: {
          nameField: 'title',
          nameTitle: $t('notice.name'),
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: [{ code: 'detail', text: $t('notice.detail') }],
      },
      field: 'operation',
      fixed: 'right',
      title: $t('notice.operation'),
      width: 120,
    },
  ];
}

