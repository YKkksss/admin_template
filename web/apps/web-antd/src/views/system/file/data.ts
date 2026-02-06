import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, VxeTableGridOptions } from '#/adapter/vxe-table';
import type { SystemFileApi } from '#/api/system/file';

import { getDeptList } from '#/api/system/dept';
import { $t } from '#/locales';

function formatSize(size: number) {
  const v = Number(size || 0);
  if (Number.isNaN(v) || v <= 0) return '0B';
  if (v < 1024) return `${v}B`;
  const kb = v / 1024;
  if (kb < 1024) return `${kb.toFixed(2)}KB`;
  const mb = kb / 1024;
  if (mb < 1024) return `${mb.toFixed(2)}MB`;
  const gb = mb / 1024;
  return `${gb.toFixed(2)}GB`;
}

export function useGridFormSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'originalName',
      label: $t('system.file.originalName'),
    },
    {
      component: 'Input',
      fieldName: 'creatorName',
      label: $t('system.file.creatorName'),
    },
    {
      component: 'ApiTreeSelect',
      componentProps: {
        allowClear: true,
        api: getDeptList,
        class: 'w-full',
        childrenField: 'children',
        labelField: 'name',
        valueField: 'id',
      },
      fieldName: 'deptId',
      label: $t('system.file.dept'),
    },
  ];
}

export function useColumns<T = SystemFileApi.SysFile>(
  onActionClick: OnActionClickFn<T>,
): VxeTableGridOptions['columns'] {
  return [
    {
      field: 'originalName',
      title: $t('system.file.originalName'),
      minWidth: 260,
    },
    {
      field: 'size',
      title: $t('system.file.size'),
      width: 120,
      formatter: ({ cellValue }: { cellValue: any }) => formatSize(cellValue),
    },
    {
      field: 'mime',
      title: $t('system.file.mime'),
      width: 180,
    },
    {
      field: 'creatorName',
      title: $t('system.file.creatorName'),
      width: 120,
    },
    {
      field: 'deptName',
      title: $t('system.file.dept'),
      width: 160,
    },
    {
      field: 'createTime',
      title: $t('system.file.createTime'),
      width: 200,
    },
    {
      align: 'center',
      cellRender: {
        attrs: {
          nameField: 'originalName',
          nameTitle: $t('system.file.name'),
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: [
          {
            code: 'preview',
            text: $t('system.file.preview'),
          },
          {
            code: 'download',
            text: $t('system.file.download'),
          },
          'delete',
        ],
      },
      field: 'operation',
      fixed: 'right',
      title: $t('system.file.operation'),
      width: 200,
    },
  ];
}

