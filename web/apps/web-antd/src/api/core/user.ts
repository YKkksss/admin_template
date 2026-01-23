import type { UserInfo } from '@vben/types';

import { requestClient } from '#/api/request';

/**
 * 获取用户信息
 */
export async function getUserInfoApi() {
  return requestClient.get<UserInfo>('/user/info');
}

export namespace UserProfileApi {
  /** 更新个人信息参数 */
  export interface UpdateProfileParams {
    avatar?: string | null;
    homePath?: string | null;
    introduction?: string | null;
    realName?: string | null;
  }

  /** 修改密码参数 */
  export interface ChangePasswordParams {
    newPassword: string;
    oldPassword: string;
  }
}

/**
 * 更新当前用户基础信息（个人中心-基本设置）
 */
export async function updateUserProfileApi(data: UserProfileApi.UpdateProfileParams) {
  return requestClient.put<UserInfo>('/user/profile', data);
}

/**
 * 修改当前用户密码（个人中心-修改密码）
 */
export async function changePasswordApi(data: UserProfileApi.ChangePasswordParams) {
  return requestClient.post<boolean>('/user/change-password', data);
}
