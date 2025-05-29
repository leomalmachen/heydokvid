import { ReactElement } from 'react';

declare module '@livekit/components-react' {
  export interface LiveKitRoomProps {
    video?: boolean;
    audio?: boolean;
    token: string;
    serverUrl: string;
    onDisconnected?: () => void;
    'data-lk-theme'?: string;
    style?: React.CSSProperties;
    children?: React.ReactNode;
  }

  export interface ParticipantTileProps {
    [key: string]: any;
  }

  export const LiveKitRoom: (props: LiveKitRoomProps) => ReactElement | null;
  export const ParticipantTile: (props: ParticipantTileProps) => ReactElement | null;
} 