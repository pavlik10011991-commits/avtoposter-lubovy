import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

// Демонстрация экрана: сверху заголовок шага, в центре запись экрана (с приближениями),
// внизу — Люба в круге (видео или фото), плашка с призывом в конце.
export type Step = {at: number; title: string};          // секунда начала шага
export type Zoom = {from: number; to: number; x: number; y: number; scale: number}; // x,y — доли 0..1
export const demoDefaults = {
  handle: '@lubov_pr_',
  topic: 'Как установить скил дизайна в Claude',
  screen: '' as string,            // файл записи экрана в public/ (mp4)
  face: '' as string,              // видео с Любой в public/ (mp4); если пусто — фото
  facePhoto: 'lubov_01.jpg',
  steps: [
    {at: 0, title: 'Шаг 1. Откройте настройки'},
    {at: 4, title: 'Шаг 2. Раздел «Навыки»'},
    {at: 8, title: 'Шаг 3. Включите скил дизайна'},
  ] as Step[],
  zooms: [] as Zoom[],
  cta: 'ХОТИТЕ ТАК ЖЕ? ПИШИТЕ В ДИРЕКТ',
  ctaFrom: 10,
};

const fonts = `
@font-face{font-family:Oswald;font-weight:700;src:url(${staticFile('oswald-latin-700-normal.woff2')})}
@font-face{font-family:Oswald;font-weight:700;src:url(${staticFile('oswald-cyrillic-700-normal.woff2')});unicode-range:U+0400-04FF,U+2116}
@font-face{font-family:Montserrat;font-weight:700;src:url(${staticFile('montserrat-latin-700-normal.woff2')})}
@font-face{font-family:Montserrat;font-weight:700;src:url(${staticFile('montserrat-cyrillic-700-normal.woff2')});unicode-range:U+0400-04FF,U+2116}`;
const CREAM = '#F4ECDF', GOLD = '#E6C9A0';

export const Demo: React.FC<typeof demoDefaults> = (p) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig(); const t = f / fps;
  const step = [...p.steps].reverse().find((s) => t >= s.at) ?? p.steps[0];
  const stepStart = step ? step.at * fps : 0;
  const pop = spring({frame: f - stepStart, fps, config: {damping: 200}});
  // приближение экрана
  let sc = 1, ox = 0.5, oy = 0.5;
  for (const z of p.zooms) {
    const k = interpolate(t, [z.from, z.from + 0.5, z.to - 0.5, z.to], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
    if (k > 0) { sc = 1 + (z.scale - 1) * k; ox = z.x; oy = z.y; }
  }
  const cta = spring({frame: f - p.ctaFrom * fps, fps, config: {damping: 200}});
  return (
    <AbsoluteFill style={{background: 'radial-gradient(circle at 50% 30%, #2a211c 0%, #0d0b0a 70%)', color: CREAM}}>
      <style>{fonts}</style>
      <div style={{position: 'absolute', top: 110, width: '100%', textAlign: 'center', font: '700 28px Montserrat', letterSpacing: '.12em', opacity: .8}}>{p.handle}</div>
      <div style={{position: 'absolute', top: 170, left: 70, right: 70, textAlign: 'center', font: '700 30px Montserrat', letterSpacing: '.28em', textTransform: 'uppercase', color: GOLD}}>{p.topic}</div>
      <div style={{position: 'absolute', top: 250, left: 60, right: 60, textAlign: 'center', fontFamily: 'Oswald', fontWeight: 700, fontSize: 84, lineHeight: 1.05, textTransform: 'uppercase',
        opacity: pop, transform: `translateY(${(1 - pop) * 30}px)`}}>{step?.title}</div>
      {/* экран */}
      <div style={{position: 'absolute', top: 470, left: 40, right: 40, height: 760, borderRadius: 28, overflow: 'hidden', border: `3px solid ${GOLD}`, background: '#1b1614', boxShadow: '0 30px 80px rgba(0,0,0,.6)'}}>
        <div style={{width: '100%', height: '100%', transform: `scale(${sc})`, transformOrigin: `${ox * 100}% ${oy * 100}%`}}>
          {p.screen ? <OffthreadVideo src={staticFile(p.screen)} muted style={{width: '100%', height: '100%', objectFit: 'contain'}} />
            : <div style={{height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', font: '700 40px Montserrat', color: '#8a7a6a', letterSpacing: '.1em'}}>ЗДЕСЬ ЗАПИСЬ ЭКРАНА</div>}
        </div>
      </div>
      {/* Люба в круге */}
      <div style={{position: 'absolute', top: 1290, left: '50%', marginLeft: -200, width: 400, height: 400, borderRadius: '50%', overflow: 'hidden', border: `6px solid ${CREAM}`, boxShadow: '0 20px 60px rgba(0,0,0,.6)'}}>
        {p.face ? <OffthreadVideo src={staticFile(p.face)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
          : <Img src={staticFile(p.facePhoto)} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '30% 25%'}} />}
      </div>
      <div style={{position: 'absolute', bottom: 90, width: '100%', textAlign: 'center', opacity: cta, transform: `scale(${0.9 + 0.1 * cta})`}}>
        <span style={{display: 'inline-block', padding: '22px 44px', borderRadius: 80, background: CREAM, color: '#1b1614', font: '700 32px Montserrat', letterSpacing: '.06em'}}>{p.cta}</span>
      </div>
    </AbsoluteFill>
  );
};
