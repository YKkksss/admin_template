import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, VxeTableGridOptions } from '#/adapter/vxe-table';
import type { MonitorLogApi } from '#/api/monitor/log';

import { $t } from '#/locales';

export function useGridFormSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'username',
      label: $t('monitor.operationLog.username'),
    },
    {
      component: 'Input',
      fieldName: 'module',
      label: $t('monitor.operationLog.module'),
    },
    {
      component: 'Select',
      componentProps: {
        allowClear: true,
        options: [
          { label: 'GET', value: 'GET' },
          { label: 'POST', value: 'POST' },
          { label: 'PUT', value: 'PUT' },
          { label: 'PATCH', value: 'PATCH' },
          { label: 'DELETE', value: 'DELETE' },
        ],
      },
      fieldName: 'method',
      label: $t('monitor.operationLog.method'),
    },
    {
      component: 'Select',
      componentProps: {
        allowClear: true,
        options: [
          { label: $t('monitor.success'), value: 1 },
          { label: $t('monitor.fail'), value: 0 },
        ],
      },
      fieldName: 'status',
      label: $t('monitor.operationLog.status'),
    },
  ];
}

export function useColumns<T = MonitorLogApi.OperationLog>(
  onActionClick: OnActionClickFn<T>,
): VxeTableGridOptions['columns'] {
  return [
    {
      field: 'username',
      title: $t('monitor.operationLog.username'),
      width: 160,
    },
    {
      field: 'module',
      title: $t('monitor.operationLog.module'),
      width: 160,
      showOverflow: true,
    },
    {
      field: 'action',
      title: $t('monitor.operationLog.action'),
      width: 120,
    },
    {
      field: 'method',
      title: $t('monitor.operationLog.method'),
      width: 100,
    },
    {
      field: 'url',
      title: $t('monitor.operationLog.url'),
      minWidth: 220,
      showOverflow: true,
    },
    {
      field: 'ip',
      title: $t('monitor.operationLog.ip'),
      width: 160,
    },
    {
      field: 'status',
      title: $t('monitor.operationLog.status'),
      width: 100,
      cellRender: {
        name: 'CellTag',
        options: [
          { color: 'success', label: $t('monitor.success'), value: 1 },
          { color: 'error', label: $t('monitor.fail'), value: 0 },
        ],
      },
    },
    {
      field: 'duration',
      title: $t('monitor.operationLog.duration'),
      width: 120,
    },
    {
      field: 'createTime',
      title: $t('monitor.operationLog.createTime'),
      width: 200,
    },
    {
      align: 'center',
      cellRender: {
        attrs: {
          nameField: 'id',
          nameTitle: $t('monitor.operationLog.title'),
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: ['delete'],
      },
      field: 'operation',
      fixed: 'right',
      title: $t('monitor.operationLog.operation'),
      width: 110,
    },
  ];
}

