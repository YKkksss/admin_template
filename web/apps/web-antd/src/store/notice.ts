import type { NotificationItem } from '@vben/layouts';

import { computed, ref, watch } from 'vue';

import { preferences } from '@vben/preferences';
import { useAccessStore } from '@vben/stores';

import { defineStore } from 'pinia';

import {
  clearBellNoticesApi,
  getBellNoticesApi,
  markInboxNoticeReadApi,
  readAllBellNoticesApi,
} from '#/api';

export const useNoticeStore = defineStore('notice', () => {
  const accessStore = useAccessStore();

  const bellNotifications = ref<NotificationItem[]>([]);
  const showDot = computed(() => bellNotifications.value.length > 0);

  async function refreshBellNotices() {
    try {
      const data = await getBellNoticesApi();
      bellNotifications.value = (data || []).map((item) => ({
        id: item.id,
        avatar: preferences.app.defaultAvatar,
        date: item.createTime,
        isRead: item.isRead,
        message: item.message,
        title: item.title,
        link: item.link ?? undefined,
      }));
    } catch {
      bellNotifications.value = [];
    }
  }

  async function clearBellNotices() {
    try {
      await clearBellNoticesApi();
    } finally {
      await refreshBellNotices();
    }
  }

  async function readAllBellNotices() {
    try {
      await readAllBellNoticesApi();
    } finally {
      await refreshBellNotices();
    }
  }

  async function markBellNoticeRead(id: number) {
    try {
      await markInboxNoticeReadApi(id);
    } finally {
      await refreshBellNotices();
    }
  }

  // WebSocket：接收新消息事件，触发铃铛刷新（开发期单实例实现）
  let noticeWs: null | WebSocket = null;
  let reconnectTimer: any = null;
  let reconnectDelay = 1500;

  function closeNoticeWs() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    reconnectDelay = 1500;
    if (noticeWs) {
      try {
        noticeWs.close();
      } catch {
        // ignore
      }
      noticeWs = null;
    }
  }

  function buildNoticeWsUrl(token: string) {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const host = window.location.host;
    return `${protocol}://${host}/api/ws/notice?token=${encodeURIComponent(token)}`;
  }

  function connectNoticeWs(token: string) {
    closeNoticeWs();

    try {
      noticeWs = new WebSocket(buildNoticeWsUrl(token));
    } catch {
      return;
    }

    noticeWs.onmessage = async (evt) => {
      try {
        const payload = JSON.parse(evt.data || '{}');
        if (payload?.event === 'notice:new') {
          await refreshBellNotices();
        }
      } catch {
        // ignore
      }
    };

    noticeWs.onclose = () => {
      // token 仍存在时尝试重连
      if (accessStore.accessToken) {
        const delay = reconnectDelay;
        reconnectDelay = Math.min(reconnectDelay * 2, 15_000);
        reconnectTimer = setTimeout(() => {
          connectNoticeWs(accessStore.accessToken as any);
        }, delay);
      }
    };
  }

  watch(
    () => accessStore.accessToken,
    async (token) => {
      if (token) {
        await refreshBellNotices();
        connectNoticeWs(token);
        return;
      }
      bellNotifications.value = [];
      closeNoticeWs();
    },
    { immediate: true },
  );

  function $reset() {
    bellNotifications.value = [];
    closeNoticeWs();
  }

  return {
    $reset,
    bellNotifications,
    clearBellNotices,
    markBellNoticeRead,
    readAllBellNotices,
    refreshBellNotices,
    showDot,
  };
});

