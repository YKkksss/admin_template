import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, VxeTableGridOptions } from '#/adapter/vxe-table';
import type { MonitorLogApi } from '#/api/monitor/log';

import { $t } from '#/locales';

export function useGridFormSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'username',
      label: $t('monitor.loginLog.username'),
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
      label: $t('monitor.loginLog.status'),
    },
  ];
}

export function useColumns<T = MonitorLogApi.LoginLog>(
  onActionClick: OnActionClickFn<T>,
): VxeTableGridOptions['columns'] {
  return [
    {
      field: 'username',
      title: $t('monitor.loginLog.username'),
      width: 180,
    },
    {
      field: 'ip',
      title: $t('monitor.loginLog.ip'),
      width: 160,
    },
    {
      field: 'browser',
      title: $t('monitor.loginLog.browser'),
      width: 180,
      showOverflow: true,
    },
    {
      field: 'os',
      title: $t('monitor.loginLog.os'),
      width: 140,
    },
    {
      field: 'status',
      title: $t('monitor.loginLog.status'),
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
      field: 'message',
      title: $t('monitor.loginLog.message'),
      minWidth: 200,
      showOverflow: true,
    },
    {
      field: 'createTime',
      title: $t('monitor.loginLog.createTime'),
      width: 200,
    },
    {
      align: 'center',
      cellRender: {
        attrs: {
          nameField: 'id',
          nameTitle: $t('monitor.loginLog.title'),
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: ['delete'],
      },
      field: 'operation',
      fixed: 'right',
      title: $t('monitor.loginLog.operation'),
      width: 110,
    },
  ];
}

