import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, VxeTableGridOptions } from '#/adapter/vxe-table';
import type { SystemConfigApi } from '#/api/system/config';

import { $t } from '#/locales';

export function useFormSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      componentProps: {
        allowClear: true,
      },
      fieldName: 'configName',
      label: $t('system.config.configName'),
      rules: 'required',
    },
    {
      component: 'Input',
      componentProps: (values) => {
        return {
          allowClear: true,
          disabled: !!values?.isBuiltin,
        };
      },
      fieldName: 'configKey',
      label: $t('system.config.configKey'),
      rules: 'required',
    },
    {
      component: 'Textarea',
      componentProps: {
        autoSize: { minRows: 3, maxRows: 6 },
      },
      fieldName: 'configValue',
      label: $t('system.config.configValue'),
      rules: 'required',
    },
    {
      component: 'RadioGroup',
      componentProps: {
        buttonStyle: 'solid',
        options: [
          { label: $t('common.enabled'), value: 1 },
          { label: $t('common.disabled'), value: 0 },
        ],
        optionType: 'button',
      },
      defaultValue: 1,
      fieldName: 'status',
      label: $t('system.config.status'),
    },
    {
      component: 'Switch',
      componentProps: {
        checkedChildren: $t('common.yes'),
        unCheckedChildren: $t('common.no'),
      },
      defaultValue: false,
      fieldName: 'isBuiltin',
      label: $t('system.config.isBuiltin'),
    },
    {
      component: 'Textarea',
      componentProps: {
        autoSize: { minRows: 2, maxRows: 4 },
      },
      fieldName: 'remark',
      label: $t('system.config.remark'),
    },
  ];
}

export function useGridFormSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'configName',
      label: $t('system.config.configName'),
    },
    {
      component: 'Input',
      fieldName: 'configKey',
      label: $t('system.config.configKey'),
    },
    {
      component: 'Select',
      componentProps: {
        allowClear: true,
        options: [
          { label: $t('common.enabled'), value: 1 },
          { label: $t('common.disabled'), value: 0 },
        ],
      },
      fieldName: 'status',
      label: $t('system.config.status'),
    },
  ];
}

export function useColumns<T = SystemConfigApi.SystemConfig>(
  onActionClick: OnActionClickFn<T>,
): VxeTableGridOptions['columns'] {
  return [
    {
      field: 'configName',
      title: $t('system.config.configName'),
      width: 200,
    },
    {
      field: 'configKey',
      title: $t('system.config.configKey'),
      width: 220,
    },
    {
      field: 'configValue',
      minWidth: 260,
      title: $t('system.config.configValue'),
      showOverflow: true,
    },
    {
      cellRender: {
        name: 'CellTag',
      },
      field: 'status',
      title: $t('system.config.status'),
      width: 100,
    },
    {
      field: 'isBuiltin',
      title: $t('system.config.isBuiltin'),
      width: 120,
      formatter: ({ cellValue }: { cellValue: any }) =>
        cellValue ? $t('common.yes') : $t('common.no'),
    },
    {
      field: 'remark',
      minWidth: 200,
      title: $t('system.config.remark'),
      showOverflow: true,
    },
    {
      field: 'createTime',
      title: $t('system.config.createTime'),
      width: 200,
    },
    {
      align: 'center',
      cellRender: {
        attrs: {
          nameField: 'configName',
          nameTitle: $t('system.config.name'),
          onClick: onActionClick,
        },
        name: 'CellOperation',
      },
      field: 'operation',
      fixed: 'right',
      title: $t('system.config.operation'),
      width: 130,
    },
  ];
}

