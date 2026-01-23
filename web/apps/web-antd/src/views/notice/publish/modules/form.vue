<script lang="ts" setup>
import { useVbenModal } from '@vben/common-ui';

import { message } from 'ant-design-vue';

import { useVbenForm } from '#/adapter/form';
import {
  getNoticeTargetDeptsApi,
  getNoticeTargetUsersApi,
  sendNoticeApi,
  type NoticeApi,
} from '#/api';
import { $t } from '#/locales';

const emit = defineEmits(['success']);

type PublishScope = 'all' | 'dept' | 'user';

const [Form, formApi] = useVbenForm({
  layout: 'vertical',
  schema: [
    {
      component: 'Input',
      componentProps: {
        allowClear: true,
        maxLength: 200,
      },
      fieldName: 'title',
      label: $t('notice.messageTitle'),
      rules: 'required',
    },
    {
      component: 'Select',
      componentProps: {
        allowClear: false,
        options: [
          { label: $t('notice.typeText.1'), value: 1 },
          { label: $t('notice.typeText.2'), value: 2 },
          { label: $t('notice.typeText.3'), value: 3 },
        ],
      },
      defaultValue: 1,
      fieldName: 'type',
      label: $t('notice.type'),
      rules: 'required',
    },
    {
      component: 'RadioGroup',
      componentProps: {
        buttonStyle: 'solid',
        optionType: 'button',
        options: [
          { label: $t('notice.publish.sendScopeText.all'), value: 'all' },
          { label: $t('notice.publish.sendScopeText.dept'), value: 'dept' },
          { label: $t('notice.publish.sendScopeText.user'), value: 'user' },
        ],
      },
      defaultValue: 'all',
      fieldName: 'scope',
      label: $t('notice.publish.sendScope'),
      rules: 'required',
    },
    {
      component: 'ApiTreeSelect',
      componentProps: {
        allowClear: true,
        api: getNoticeTargetDeptsApi,
        childrenField: 'children',
        class: 'w-full',
        labelField: 'name',
        multiple: true,
        showSearch: true,
        treeCheckable: true,
        treeDefaultExpandAll: true,
        valueField: 'id',
      },
      dependencies: {
        show: (values) => values.scope === 'dept',
        triggerFields: ['scope'],
      },
      fieldName: 'deptIds',
      label: $t('notice.publish.deptIds'),
    },
    {
      component: 'ApiSelect',
      componentProps: {
        allowClear: true,
        api: getNoticeTargetUsersApi,
        class: 'w-full',
        labelField: 'name',
        mode: 'multiple',
        showSearch: true,
        valueField: 'id',
      },
      dependencies: {
        show: (values) => values.scope === 'user',
        triggerFields: ['scope'],
      },
      fieldName: 'userIds',
      label: $t('notice.publish.userIds'),
    },
    {
      component: 'Textarea',
      componentProps: {
        maxLength: 500,
        rows: 3,
        showCount: true,
      },
      fieldName: 'message',
      label: $t('notice.summary'),
    },
    {
      component: 'Textarea',
      componentProps: {
        rows: 6,
      },
      fieldName: 'content',
      label: $t('notice.content'),
      rules: 'required',
    },
    {
      component: 'Input',
      componentProps: {
        allowClear: true,
        maxLength: 500,
      },
      fieldName: 'link',
      label: $t('notice.publish.link'),
    },
  ],
  showDefaultActions: false,
});

function resetForm() {
  formApi.resetForm();
  formApi.setValues({
    scope: 'all',
    type: 1,
    deptIds: [],
    userIds: [],
  });
}

const [Modal, modalApi] = useVbenModal({
  async onConfirm() {
    const { valid } = await formApi.validate();
    if (!valid) {
      return;
    }

    const values = await formApi.getValues();
    const scope = (values.scope || 'all') as PublishScope;
    const deptIds = Array.isArray(values.deptIds) ? values.deptIds : [];
    const userIds = Array.isArray(values.userIds) ? values.userIds : [];

    const payload: NoticeApi.SendNoticeParams = {
      title: String(values.title ?? '').trim(),
      content: String(values.content ?? '').trim(),
      message: values.message ? String(values.message).trim() : undefined,
      type: (values.type ?? 1) as NoticeApi.NoticeType,
      link: values.link ? String(values.link).trim() : undefined,
      sendAll: scope === 'all',
      deptIds: scope === 'dept' ? deptIds.map((v: any) => Number(v)) : [],
      userIds: scope === 'user' ? userIds.map((v: any) => Number(v)) : [],
    };

    if (!payload.sendAll && payload.deptIds.length === 0 && payload.userIds.length === 0) {
      message.warning($t('notice.publish.selectReceiver'));
      return;
    }

    modalApi.lock();
    try {
      await sendNoticeApi(payload);
      message.success($t('notice.publish.sendSuccess'));
      modalApi.close();
      emit('success');
    } finally {
      modalApi.lock(false);
    }
  },
  onOpenChange(isOpen) {
    if (!isOpen) {
      return;
    }
    resetForm();
  },
});
</script>

<template>
  <Modal :title="$t('notice.publish.publish')">
    <Form class="mx-4" />
  </Modal>
</template>
