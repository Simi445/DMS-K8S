export type User = {
  user_id: number;
  username: string;
  email: string;
  role: string;
};

export type Device = {
  device_id: number,
  user_id: number;
  name: string;
  status: string;
  maxConsumption: number;
};


export type JWTPayload = {
    user_id?: number;
    username?: string;
    email?: string;
    role?: string;
    exp?: number;
  };