import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, VxeTableGridOptions } from '#/adapter/vxe-table';
import type { SystemDictApi } from '#/api/system/dict';

import { $t } from '#/locales';

export function useFormSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      componentProps: {
        allowClear: true,
      },
      fieldName: 'name',
      label: $t('system.dict.type.name'),
      rules: 'required',
    },
    {
      component: 'Input',
      componentProps: (values) => {
        return {
          allowClear: true,
          disabled: !!values?.id,
        };
      },
      fieldName: 'code',
      label: $t('system.dict.type.code'),
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
      label: $t('system.dict.type.status'),
    },
    {
      component: 'Textarea',
      componentProps: {
        autoSize: { minRows: 2, maxRows: 4 },
      },
      fieldName: 'remark',
      label: $t('system.dict.type.remark'),
    },
  ];
}

export function useGridFormSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'name',
      label: $t('system.dict.type.name'),
    },
    {
      component: 'Input',
      fieldName: 'code',
      label: $t('system.dict.type.code'),
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
      label: $t('system.dict.type.status'),
    },
  ];
}

export function useColumns<T = SystemDictApi.DictType>(
  onActionClick: OnActionClickFn<T>,
): VxeTableGridOptions['columns'] {
  return [
    {
      field: 'name',
      title: $t('system.dict.type.name'),
      width: 200,
    },
    {
      field: 'code',
      title: $t('system.dict.type.code'),
      width: 220,
    },
    {
      cellRender: {
        name: 'CellTag',
      },
      field: 'status',
      title: $t('system.dict.type.status'),
      width: 100,
    },
    {
      field: 'remark',
      minWidth: 200,
      title: $t('system.dict.type.remark'),
      showOverflow: true,
    },
    {
      field: 'createTime',
      title: $t('system.dict.type.createTime'),
      width: 200,
    },
    {
      align: 'center',
      cellRender: {
        attrs: {
          nameField: 'name',
          nameTitle: $t('system.dict.type.title'),
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: [{ code: 'dictData', text: $t('system.dict.data.title') }, 'edit', 'delete'],
      },
      field: 'operation',
      fixed: 'right',
      title: $t('system.dict.type.operation'),
      width: 200,
    },
  ];
}
