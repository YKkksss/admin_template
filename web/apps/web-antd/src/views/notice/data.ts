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
          { label: $t('notice.readStatusFilter.all'), value: 'all' },
          { label: $t('notice.readStatusFilter.unread'), value: 'unread' },
          { label: $t('notice.readStatusFilter.read'), value: 'read' },
        ],
      },
      defaultValue: 'all',
      fieldName: 'readStatus',
      label: $t('notice.readStatus'),
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

export function useColumns<T = NoticeApi.InboxItem>(
  onActionClick: OnActionClickFn<T>,
): VxeTableGridOptions['columns'] {
  return [
    {
      type: 'checkbox',
      width: 48,
    },
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
      field: 'isRead',
      title: $t('notice.readStatus'),
      width: 100,
      cellRender: {
        name: 'CellTag',
        options: [
          { color: 'success', label: $t('notice.readText.read'), value: true },
          { color: 'error', label: $t('notice.readText.unread'), value: false },
        ],
      },
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
        options: [{ code: 'detail', text: $t('notice.detail') }, 'delete'],
      },
      field: 'operation',
      fixed: 'right',
      title: $t('notice.operation'),
      width: 140,
    },
  ];
}

