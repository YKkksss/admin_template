<script lang="ts" setup>
import type { SystemUserApi } from '#/api/system/user';

import { computed, ref } from 'vue';

import { useVbenModal } from '@vben/common-ui';

import { Button, message } from 'ant-design-vue';

import { useVbenForm } from '#/adapter/form';
import { z } from '#/adapter/form';
import { resetUserPassword } from '#/api/system/user';
import { $t } from '#/locales';

const emit = defineEmits(['success']);

const userData = ref<SystemUserApi.SystemUser>();

const [Form, formApi] = useVbenForm({
  layout: 'vertical',
  schema: [
    {
      component: 'InputPassword',
      componentProps: {
        allowClear: true,
        autocomplete: 'new-password',
      },
      fieldName: 'password',
      label: $t('system.user.password'),
      rules: z
        .string()
        .min(6, $t('ui.formRules.minLength', [$t('system.user.password'), 6])),
    },
  ],
  showDefaultActions: false,
});

const getTitle = computed(() => {
  if (userData.value?.username) {
    return `${$t('system.user.resetPassword')}：${userData.value.username}`;
  }
  return $t('system.user.resetPassword');
});

const [Modal, modalApi] = useVbenModal({
  async onConfirm() {
    const { valid } = await formApi.validate();
    if (!valid) return;

    const values = await formApi.getValues();
    const userId = userData.value?.id;
    if (!userId) return;

    modalApi.lock();
    try {
      await resetUserPassword(userId, values.password);
      modalApi.close();
      emit('success');
    } catch (err: any) {
      message.error(err?.message || '操作失败');
      modalApi.lock(false);
    }
  },
  onOpenChange(isOpen) {
    if (!isOpen) {
      return;
    }
    formApi.resetForm();
    userData.value = modalApi.getData<SystemUserApi.SystemUser>();
  },
});
</script>

<template>
  <Modal :title="getTitle">
    <Form class="mx-4" />
    <template #prepend-footer>
      <div class="flex-auto">
        <Button type="primary" danger @click="formApi.resetForm()">
          {{ $t('common.reset') }}
        </Button>
      </div>
    </template>
  </Modal>
</template>

