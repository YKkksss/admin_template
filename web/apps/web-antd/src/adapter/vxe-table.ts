import type { VxeTableGridOptions } from '@vben/plugins/vxe-table';
import type { Recordable } from '@vben/types';

import type { ComponentType } from './component';

import type { SlotsType } from 'vue';

import { defineComponent, h, resolveDirective, withDirectives } from 'vue';

import { Download, IconifyIcon, Upload as UploadIcon } from '@vben/icons';
import { $te } from '@vben/locales';
import {
  setupVbenVxeTable,
  useVbenVxeGrid as useGrid,
} from '@vben/plugins/vxe-table';
import { get, isFunction, isString } from '@vben/utils';

import { objectOmit } from '@vueuse/core';
import { Button, Image, Modal, Popconfirm, Switch, Tag, Upload, message } from 'ant-design-vue';

import { requestClient } from '#/api/request';
import { $t } from '#/locales';
import { downloadBlobWithAuth } from '#/utils/download';

import { useVbenForm } from './form';

setupVbenVxeTable({
  configVxeTable: (vxeUI) => {
    vxeUI.setConfig({
      grid: {
        align: 'center',
        border: false,
        columnConfig: {
          resizable: true,
        },

        formConfig: {
          // 全局禁用 vxe-table 的表单配置，使用 formOptions
          enabled: false,
        },
        minHeight: 180,
        proxyConfig: {
          autoLoad: true,
          response: {
            result: 'items',
            total: 'total',
            list: '',
          },
          showActiveMsg: true,
          showResponseMsg: false,
        },
        round: true,
        showOverflow: true,
        size: 'small',
      } as VxeTableGridOptions,
    });

    /**
     * 解决 vxeTable 在热更新时可能会出错的问题
     */
    vxeUI.renderer.forEach((_item, key) => {
      if (key.startsWith('Cell')) {
        vxeUI.renderer.delete(key);
      }
    });

    // 表格配置项可以用 cellRender: { name: 'CellImage' },
    vxeUI.renderer.add('CellImage', {
      renderTableDefault(renderOpts, params) {
        const { props } = renderOpts;
        const { column, row } = params;
        return h(Image, { src: row[column.field], ...props });
      },
    });

    // 表格配置项可以用 cellRender: { name: 'CellLink' },
    vxeUI.renderer.add('CellLink', {
      renderTableDefault(renderOpts) {
        const { props } = renderOpts;
        return h(
          Button,
          { size: 'small', type: 'link' },
          { default: () => props?.text },
        );
      },
    });

    // 单元格渲染：Tag
    vxeUI.renderer.add('CellTag', {
      renderTableDefault({ options, props }, { column, row }) {
        const value = get(row, column.field);
        const tagOptions = options ?? [
          { color: 'success', label: $t('common.enabled'), value: 1 },
          { color: 'error', label: $t('common.disabled'), value: 0 },
        ];
        const tagItem = tagOptions.find((item) => item.value === value);
        return h(
          Tag,
          {
            ...props,
            ...objectOmit(tagItem ?? {}, ['label']),
          },
          { default: () => tagItem?.label ?? value },
        );
      },
    });

    // 单元格渲染：开关
    vxeUI.renderer.add('CellSwitch', {
      renderTableDefault({ attrs, props }, { column, row }) {
        const loadingKey = `__loading_${column.field}`;
        const finallyProps = {
          checkedChildren: $t('common.enabled'),
          checkedValue: 1,
          unCheckedChildren: $t('common.disabled'),
          unCheckedValue: 0,
          ...props,
          checked: row[column.field],
          loading: row[loadingKey] ?? false,
          'onUpdate:checked': onChange,
        };
        async function onChange(newVal: any) {
          row[loadingKey] = true;
          try {
            const result = await attrs?.beforeChange?.(newVal, row);
            if (result !== false) {
              row[column.field] = newVal;
            }
          } finally {
            row[loadingKey] = false;
          }
        }
        return h(Switch, finallyProps);
      },
    });

    /**
     * 注册表格的操作按钮渲染器
     */
    vxeUI.renderer.add('CellOperation', {
      renderTableDefault({ attrs, options, props }, { column, row }) {
        const defaultProps = { size: 'small', type: 'link', ...props };
        let align = 'end';
        switch (column.align) {
          case 'center': {
            align = 'center';
            break;
          }
          case 'left': {
            align = 'start';
            break;
          }
          default: {
            align = 'end';
            break;
          }
        }
        const presets: Recordable<Recordable<any>> = {
          delete: {
            danger: true,
            text: $t('common.delete'),
          },
          edit: {
            text: $t('common.edit'),
          },
        };
        const operations: Array<Recordable<any>> = (options || ['edit', 'delete'])
          .map((opt) => {
            if (isString(opt)) {
              return presets[opt]
                ? { code: opt, ...presets[opt], ...defaultProps }
                : {
                    code: opt,
                    text: $te(`common.${opt}`) ? $t(`common.${opt}`) : opt,
                    ...defaultProps,
                  };
            } else {
              return { ...defaultProps, ...presets[opt.code], ...opt };
            }
          })
          .map((opt) => {
            const optBtn: Recordable<any> = {};
            Object.keys(opt).forEach((key) => {
              optBtn[key] = isFunction(opt[key]) ? opt[key](row) : opt[key];
            });
            return optBtn;
          })
          .filter((opt) => opt.show !== false);

        function renderBtn(opt: Recordable<any>, listen = true) {
          return h(
            Button,
            {
              ...props,
              ...opt,
              icon: undefined,
              onClick: listen
                ? () =>
                    attrs?.onClick?.({
                      code: opt.code,
                      row,
                    })
                : undefined,
            },
            {
              default: () => {
                const content = [];
                if (opt.icon) {
                  content.push(
                    h(IconifyIcon, { class: 'size-5', icon: opt.icon }),
                  );
                }
                content.push(opt.text);
                return content;
              },
            },
          );
        }

        function renderConfirm(opt: Recordable<any>) {
          let viewportWrapper: HTMLElement | null = null;
          return h(
            Popconfirm,
            {
              getPopupContainer(el) {
                viewportWrapper = el.closest('.vxe-table--viewport-wrapper');
                return document.body;
              },
              placement: 'topLeft',
              title: $t('ui.actionTitle.delete', [attrs?.nameTitle || '']),
              ...props,
              ...opt,
              icon: undefined,
              onOpenChange: (open: boolean) => {
                // 当弹窗打开时，禁用表格的滚动
                if (open) {
                  viewportWrapper?.style.setProperty('pointer-events', 'none');
                } else {
                  viewportWrapper?.style.removeProperty('pointer-events');
                }
              },
              onConfirm: () => {
                attrs?.onClick?.({
                  code: opt.code,
                  row,
                });
              },
            },
            {
              default: () => renderBtn({ ...opt }, false),
              description: () =>
                h(
                  'div',
                  { class: 'truncate' },
                  $t('ui.actionMessage.deleteConfirm', [
                    row[attrs?.nameField || 'name'],
                  ]),
                ),
            },
          );
        }

        const btns = operations.map((opt) =>
          opt.code === 'delete' ? renderConfirm(opt) : renderBtn(opt),
        );
        return h(
          'div',
          {
            class: 'flex table-operations',
            style: { justifyContent: align },
          },
          btns,
        );
      },
    });
  },
  useVbenForm,
});

export type ExcelImportToolbarOptions = {
  /** 是否显示导入相关按钮 */
  show?: boolean;
  /** 权限码（v-access:code） */
  authCode?: string;
  /** 导入接口地址（POST，multipart/form-data） */
  url?: string;
  /** 上传字段名，默认 file */
  fieldName?: string;
  /** 允许选择的文件类型，默认 .xlsx */
  accept?: string;

  /** 是否显示“下载模板”按钮 */
  showTemplate?: boolean;
  /** 模板下载地址（GET） */
  templateUrl?: string;
  /** 模板文件名 */
  templateFilename?: string;

  /** 是否展示默认导入结果弹窗 */
  showResultModal?: boolean;
  /** 弹窗最多展示多少条错误明细 */
  maxErrorLines?: number;
};

export type ExcelExportToolbarOptions = {
  /** 是否显示导出按钮 */
  show?: boolean;
  /** 权限码（v-access:code） */
  authCode?: string;
  /** 导出接口地址（GET） */
  url?: string;
  /** 导出文件名 */
  filename?: string;
  /** 是否拼接当前搜索条件（使用 form 最新提交值） */
  withFormValues?: boolean;
};

export type ExcelToolbarOptions = {
  import?: ExcelImportToolbarOptions;
  export?: ExcelExportToolbarOptions;
};

type ImportResult = {
  total: number;
  success: number;
  failed: number;
  errors?: Array<{ row: number; message: string; column?: string | null }>;
};

function normalizeSlotResult(result: any) {
  if (!result) return [];
  return Array.isArray(result) ? result : [result];
}

function withAccessCode(vnode: any, code?: string) {
  if (!code) return vnode;
  const dir = resolveDirective('access');
  if (!dir) return vnode;
  return withDirectives(vnode, [[dir as any, code, 'code']]);
}

export const useVbenVxeGrid = <T extends Record<string, any>>(
  options: Parameters<typeof useGrid<T, ComponentType>>[0] & {
    excel?: ExcelToolbarOptions;
  },
) => {
  const { excel, ...rest } = options as any;
  const [BaseGrid, gridApi] = useGrid<T, ComponentType>(rest);

  // 未配置 excel 时保持完全一致的行为与渲染
  if (!excel) {
    return [BaseGrid, gridApi] as const;
  }

  const excelImport = excel.import ?? {};
  const excelExport = excel.export ?? {};

  const Grid = defineComponent(
    (props: any, ctx: any) => {
      const { attrs, slots } = ctx;

      async function getLatestFormValues() {
        try {
          const fn = (gridApi as any)?.formApi?.getLatestSubmissionValues;
          if (typeof fn === 'function') {
            return (await fn()) ?? {};
          }
        } catch {}
        return {};
      }

      async function onDownloadTemplate() {
        if (!excelImport.templateUrl) return;
        const filename = excelImport.templateFilename || '导入模板.xlsx';
        try {
          await downloadBlobWithAuth(excelImport.templateUrl, filename);
        } catch (err: any) {
          message.error(err?.message || '下载失败');
        }
      }

      async function onImport(options: any) {
        const file = options?.file as File;
        if (!file) {
          options?.onError?.(new Error('文件不能为空'));
          return;
        }
        const importUrl = excelImport.url;
        if (!importUrl) {
          options?.onError?.(new Error('未配置导入接口地址'));
          return;
        }

        const fieldName = excelImport.fieldName || 'file';
        const formData = new FormData();
        formData.append(fieldName, file);

        try {
          const res = await requestClient.post<ImportResult>(importUrl, formData);
          options?.onSuccess?.({}, file);

          // 默认展示导入结果
          const showResult = excelImport.showResultModal !== false;
          if (showResult) {
            if (res.failed && res.errors?.length) {
              const maxLines = excelImport.maxErrorLines ?? 20;
              const top = res.errors.slice(0, maxLines);
              const lines: string[] = [
                `总计：${res.total}`,
                `成功：${res.success}`,
                `失败：${res.failed}`,
                '',
                `失败明细（最多展示 ${maxLines} 条）：`,
                ...top.map((e) => {
                  const col = e.column ? `（${e.column}）` : '';
                  return `第 ${e.row} 行${col}：${e.message}`;
                }),
              ];
              if (res.errors.length > top.length) {
                lines.push('...');
              }
              Modal.warning({
                title: $t('common.importResult'),
                content: () =>
                  h(
                    'pre',
                    { style: 'white-space: pre-wrap; margin: 0;' },
                    lines.join('\n'),
                  ),
              });
            } else {
              message.success($t('common.importDone'));
            }
          }

          try {
            (gridApi as any)?.query?.();
          } catch {}
        } catch (err) {
          // 错误提示已由 requestClient 的拦截器统一处理，这里只通知 Upload 失败
          options?.onError?.(err);
        }
      }

      async function onExport() {
        const exportUrl = excelExport.url;
        if (!exportUrl) return;

        const withForm = excelExport.withFormValues !== false;
        const formValues = withForm ? await getLatestFormValues() : {};
        const params = new URLSearchParams();

        Object.entries(formValues || {}).forEach(([k, v]) => {
          if (v === undefined || v === null || v === '') return;
          if (Array.isArray(v)) {
            v.forEach((item) => {
              if (item === undefined || item === null || item === '') return;
              params.append(k, String(item));
            });
            return;
          }
          params.append(k, String(v));
        });

        const qs = params.toString();
        const url = `${exportUrl}${qs ? `?${qs}` : ''}`;
        const filename = excelExport.filename || '导出.xlsx';

        try {
          await downloadBlobWithAuth(url, filename);
        } catch (err: any) {
          message.error(err?.message || $t('common.exportFailed'));
        }
      }

      function renderExcelActions() {
        const nodes: any[] = [];

        const showImport = excelImport.show !== false && !!excelImport.url;
        const showTemplate =
          showImport &&
          (excelImport.showTemplate !== false) &&
          !!excelImport.templateUrl;
        const showExport = excelExport.show !== false && !!excelExport.url;

        if (!showImport && !showExport) return [];

        if (showTemplate) {
          nodes.push(
            withAccessCode(
              h(
                Button,
                { onClick: onDownloadTemplate },
                {
                  default: () => [
                    h(Download, { class: 'mr-1 size-4' }),
                    $t('common.downloadTemplate'),
                  ],
                },
              ),
              excelImport.authCode,
            ),
          );
        }

        if (showImport) {
          nodes.push(
            withAccessCode(
              h(
                Upload,
                {
                  accept: excelImport.accept || '.xlsx',
                  customRequest: onImport,
                  maxCount: 1,
                  showUploadList: false,
                },
                {
                  default: () =>
                    h(Button, {}, {
                      default: () => [
                        h(UploadIcon, { class: 'mr-1 size-4' }),
                        $t('common.import'),
                      ],
                    }),
                },
              ),
              excelImport.authCode,
            ),
          );
        }

        if (showExport) {
          nodes.push(
            withAccessCode(
              h(Button, { onClick: onExport }, {
                default: () => [
                  h(Download, { class: 'mr-1 size-4' }),
                  $t('common.export'),
                ],
              }),
              excelExport.authCode,
            ),
          );
        }

        return [
          h('div', { class: 'flex items-center gap-2.5' }, nodes.filter(Boolean)),
        ];
      }

      const mergedSlots: any = { ...slots };
      mergedSlots['toolbar-actions'] = (slotProps: any) => {
        const original = normalizeSlotResult(slots['toolbar-actions']?.(slotProps));
        const extra = renderExcelActions();
        if (!original.length && !extra.length) return;
        if (!extra.length) return original;
        if (!original.length) return extra;
        return [
          h('div', { class: 'flex items-center gap-2.5' }, [
            ...original,
            ...extra,
          ]),
        ];
      };

      return () => h(BaseGrid as any, { ...props, ...attrs }, mergedSlots);
    },
    {
      name: 'VbenVxeGridWithExcel',
      inheritAttrs: false,
      slots: Object as SlotsType<
        {
          'table-title': any;
          'toolbar-actions': any;
          'toolbar-tools': any;
        } & Record<string, any>
      >,
    },
  );

  return [Grid as unknown as typeof BaseGrid, gridApi] as const;
};

export type OnActionClickParams<T = Recordable<any>> = {
  code: string;
  row: T;
};
export type OnActionClickFn<T = Recordable<any>> = (
  params: OnActionClickParams<T>,
) => void;
export type * from '@vben/plugins/vxe-table';
