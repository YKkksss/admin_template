import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, VxeTableGridOptions } from '#/adapter/vxe-table';
import type { SystemSessionApi } from '#/api/system/session';

import { $t } from '#/locales';

export function useGridFormSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'username',
      label: $t('system.session.username'),
    },
    {
      component: 'Input',
      fieldName: 'ip',
      label: $t('system.session.ip'),
    },
    {
      component: 'Select',
      componentProps: {
        allowClear: true,
        options: [
          { label: $t('system.session.statusText.online'), value: 1 },
          { label: $t('system.session.statusText.offline'), value: 0 },
        ],
      },
      fieldName: 'status',
      label: $t('system.session.status'),
    },
  ];
}

export function useColumns<T = SystemSessionApi.Session>(
  onActionClick: OnActionClickFn<T>,
): VxeTableGridOptions['columns'] {
  return [
    {
      field: 'username',
      title: $t('system.session.username'),
      width: 140,
    },
    {
      field: 'ip',
      title: $t('system.session.ip'),
      width: 150,
    },
    {
      field: 'browser',
      title: $t('system.session.browser'),
      width: 180,
      showOverflow: true,
    },
    {
      field: 'os',
      title: $t('system.session.os'),
      width: 120,
    },
    {
      field: 'loginTime',
      title: $t('system.session.loginTime'),
      width: 180,
    },
    {
      field: 'lastActiveTime',
      title: $t('system.session.lastActiveTime'),
      width: 180,
    },
    {
      field: 'expireTime',
      title: $t('system.session.expireTime'),
      width: 180,
    },
    {
      field: 'isCurrent',
      title: $t('system.session.isCurrent'),
      width: 110,
      formatter: ({ cellValue }: { cellValue: any }) =>
        cellValue ? $t('common.yes') : $t('common.no'),
    },
    {
      cellRender: {
        name: 'CellTag',
        options: [
          { color: 'success', label: $t('system.session.statusText.online'), value: 1 },
          { color: 'default', label: $t('system.session.statusText.offline'), value: 0 },
        ],
      },
      field: 'status',
      title: $t('system.session.status'),
      width: 120,
    },
    {
      align: 'center',
      cellRender: {
        attrs: {
          nameField: 'username',
          nameTitle: $t('system.session.title'),
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: [
          {
            code: 'kick',
            danger: true,
            text: $t('system.session.kick'),
            disabled: (row: SystemSessionApi.Session) =>
              !!row.isCurrent || row.status === 0,
          },
        ],
      },
      field: 'operation',
      fixed: 'right',
      title: $t('system.session.operation'),
      width: 120,
    },
  ];
}

