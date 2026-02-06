import type { NotificationItem } from '@vben/layouts';

import { computed, ref, watch } from 'vue';

import { preferences } from '@vben/preferences';
import { useAccessStore } from '@vben/stores';

import { notification } from 'ant-design-vue';
import { defineStore } from 'pinia';

import {
  clearBellNoticesApi,
  getBellNoticesApi,
  getUnreadCountApi,
  markInboxNoticeReadApi,
  readAllBellNoticesApi,
} from '#/api';
import { $t } from '#/locales';

import { useAuthStore } from './auth';

export const useNoticeStore = defineStore('notice', () => {
  const accessStore = useAccessStore();
  const authStore = useAuthStore();

  const bellNotifications = ref<NotificationItem[]>([]);
  const unreadCount = ref(0);
  const bellUnreadCount = ref(0);
  const showDot = computed(() => bellUnreadCount.value > 0);

  async function refreshUnreadCount() {
    try {
      const data = await getUnreadCountApi();
      unreadCount.value = Number(data?.unread || 0);
      bellUnreadCount.value = Number(data?.bellUnread || 0);
    } catch {
      // 未读统计获取失败时，降级使用铃铛列表长度（不包含已被铃铛隐藏的未读）
      unreadCount.value = bellNotifications.value.length;
      bellUnreadCount.value = bellNotifications.value.length;
    }
  }

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
    } finally {
      await refreshUnreadCount();
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
        if (payload?.event === 'auth:kickout') {
          const reason = payload?.data?.reason || '已被强制下线，请重新登录';
          notification.warning({
            message: $t('system.session.kickoutTitle'),
            description: reason,
            duration: 3,
          });

          // 与 request 拦截器的重新认证逻辑保持一致
          accessStore.setAccessToken(null);
          if (
            preferences.app.loginExpiredMode === 'modal' &&
            accessStore.isAccessChecked
          ) {
            accessStore.setLoginExpired(true);
          } else {
            await authStore.logout();
          }
          return;
        }
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
      unreadCount.value = 0;
      bellUnreadCount.value = 0;
      closeNoticeWs();
    },
    { immediate: true },
  );

  function $reset() {
    bellNotifications.value = [];
    unreadCount.value = 0;
    bellUnreadCount.value = 0;
    closeNoticeWs();
  }

  return {
    $reset,
    bellNotifications,
    bellUnreadCount,
    clearBellNotices,
    markBellNoticeRead,
    readAllBellNotices,
    refreshBellNotices,
    refreshUnreadCount,
    showDot,
    unreadCount,
  };
});
