import { useAppConfig } from '@vben/hooks';
import { preferences } from '@vben/preferences';
import { useAccessStore } from '@vben/stores';

const { apiURL } = useAppConfig(import.meta.env, import.meta.env.PROD);

function joinUrl(base: string, path: string) {
  const b = base.endsWith('/') ? base.slice(0, -1) : base;
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${b}${p}`;
}

function formatAuthHeader(token: null | string) {
  return token ? `Bearer ${token}` : '';
}

export async function fetchBlobWithAuth(pathOrUrl: string) {
  const accessStore = useAccessStore();
  const url = /^https?:\/\//.test(pathOrUrl) ? pathOrUrl : joinUrl(apiURL, pathOrUrl);

  const resp = await fetch(url, {
    headers: {
      Authorization: formatAuthHeader(accessStore.accessToken),
      'Accept-Language': preferences.app.locale,
    },
  });

  if (!resp.ok) {
    const text = await resp.text();
    let msg = text || '请求失败';
    try {
      const json = JSON.parse(text || '{}');
      msg = json?.error || json?.message || msg;
    } catch {}
    throw new Error(msg);
  }

  return resp.blob();
}

export async function downloadBlobWithAuth(
  pathOrUrl: string,
  filename: string,
) {
  const blob = await fetchBlobWithAuth(pathOrUrl);
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename || 'download';
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

