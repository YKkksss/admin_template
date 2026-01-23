import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, VxeTableGridOptions } from '#/adapter/vxe-table';
import type { SystemDictApi } from '#/api/system/dict';

import { getDictTypeOptions } from '#/api/system/dict';
import { $t } from '#/locales';

export function useFormSchema(): VbenFormSchema[] {
  return [
    {
      component: 'ApiSelect',
      componentProps: {
        allowClear: false,
        api: getDictTypeOptions,
        class: 'w-full',
        labelField: 'name',
        valueField: 'code',
      },
      fieldName: 'typeCode',
      label: $t('system.dict.data.typeCode'),
      rules: 'required',
    },
    {
      component: 'Input',
      componentProps: {
        allowClear: true,
      },
      fieldName: 'label',
      label: $t('system.dict.data.label'),
      rules: 'required',
    },
    {
      component: 'Input',
      componentProps: {
        allowClear: true,
      },
      fieldName: 'value',
      label: $t('system.dict.data.value'),
      rules: 'required',
    },
    {
      component: 'InputNumber',
      defaultValue: 0,
      fieldName: 'sort',
      label: $t('system.dict.data.sort'),
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
      label: $t('system.dict.data.status'),
    },
    {
      component: 'Input',
      componentProps: {
        allowClear: true,
      },
      fieldName: 'style',
      label: $t('system.dict.data.style'),
    },
    {
      component: 'Textarea',
      componentProps: {
        autoSize: { minRows: 2, maxRows: 4 },
      },
      fieldName: 'remark',
      label: $t('system.dict.data.remark'),
    },
  ];
}

export function useGridFormSchema(fixedTypeCode?: string): VbenFormSchema[] {
  const locked = !!fixedTypeCode;
  return [
    {
      component: 'ApiSelect',
      componentProps: {
        allowClear: !locked,
        api: getDictTypeOptions,
        class: 'w-full',
        disabled: locked,
        labelField: 'name',
        valueField: 'code',
      },
      defaultValue: fixedTypeCode,
      fieldName: 'typeCode',
      label: $t('system.dict.data.typeCode'),
    },
    {
      component: 'Input',
      fieldName: 'label',
      label: $t('system.dict.data.label'),
    },
    {
      component: 'Input',
      fieldName: 'value',
      label: $t('system.dict.data.value'),
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
      label: $t('system.dict.data.status'),
    },
  ];
}

export function useColumns<T = SystemDictApi.DictData>(
  onActionClick: OnActionClickFn<T>,
): VxeTableGridOptions['columns'] {
  return [
    {
      field: 'typeCode',
      title: $t('system.dict.data.typeCode'),
      width: 200,
    },
    {
      field: 'label',
      title: $t('system.dict.data.label'),
      width: 180,
    },
    {
      field: 'value',
      title: $t('system.dict.data.value'),
      width: 180,
    },
    {
      field: 'sort',
      title: $t('system.dict.data.sort'),
      width: 100,
    },
    {
      cellRender: {
        name: 'CellTag',
      },
      field: 'status',
      title: $t('system.dict.data.status'),
      width: 100,
    },
    {
      field: 'style',
      title: $t('system.dict.data.style'),
      width: 160,
      showOverflow: true,
    },
    {
      field: 'remark',
      minWidth: 200,
      title: $t('system.dict.data.remark'),
      showOverflow: true,
    },
    {
      field: 'createTime',
      title: $t('system.dict.data.createTime'),
      width: 200,
    },
    {
      align: 'center',
      cellRender: {
        attrs: {
          nameField: 'label',
          nameTitle: $t('system.dict.data.title'),
          onClick: onActionClick,
        },
        name: 'CellOperation',
      },
      field: 'operation',
      fixed: 'right',
      title: $t('system.dict.data.operation'),
      width: 130,
    },
  ];
}
