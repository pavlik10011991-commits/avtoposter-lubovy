import React from 'react';
import {AbsoluteFill, Img, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

const fonts = `
@font-face{font-family:Oswald;font-weight:700;src:url(${staticFile('oswald-latin-700-normal.woff2')})}
@font-face{font-family:Oswald;font-weight:700;src:url(${staticFile('oswald-cyrillic-700-normal.woff2')});unicode-range:U+0400-04FF,U+2116}
@font-face{font-family:Montserrat;font-weight:700;src:url(${staticFile('montserrat-latin-700-normal.woff2')})}
@font-face{font-family:Montserrat;font-weight:700;src:url(${staticFile('montserrat-cyrillic-700-normal.woff2')});unicode-range:U+0400-04FF,U+2116}
@font-face{font-family:Montserrat;font-weight:500;src:url(${staticFile('montserrat-latin-500-normal.woff2')})}
@font-face{font-family:Montserrat;font-weight:500;src:url(${staticFile('montserrat-cyrillic-500-normal.woff2')});unicode-range:U+0400-04FF,U+2116}
@font-face{font-family:'PT Serif';font-style:italic;src:url(${staticFile('pt-serif-latin-400-italic.woff2')})}
@font-face{font-family:'PT Serif';font-style:italic;src:url(${staticFile('pt-serif-cyrillic-400-italic.woff2')});unicode-range:U+0400-04FF,U+2116}`;

type Scene = {photo: string; label: string; head: string; sub: string};
export const reelSchemaDefaults = {
  handle: '@lubov_pr_',
  cta: 'ПИШИТЕ В ДИРЕКТ',
  scenes: [
    {photo: 'lubov_01.jpg', label: 'новый формат', head: 'Я не учу ИИ', sub: 'Я внедряю его в ваш бизнес — за вас, руками'},
    {photo: 'lubov_02_cafe.jpg', label: 'бесплатно · 15 минут', head: 'Покажу на вашем бизнесе', sub: 'что ИИ может делать именно у вас'},
  ] as Scene[],
};

const SceneView: React.FC<{s: Scene; dur: number; handle: string; cta?: string}> = ({s, dur, handle, cta}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const zoom = interpolate(f, [0, dur], [1.08, 1]);
  const up = (d: number) => spring({frame: f - d, fps, config: {damping: 200}});
  const fadeOut = interpolate(f, [dur - 10, dur], [1, 0], {extrapolateLeft: 'clamp'});
  const tr = (d: number) => ({opacity: up(d), transform: `translateY(${(1 - up(d)) * 60}px)`});
  return (
    <AbsoluteFill style={{opacity: fadeOut, background: '#000'}}>
      <Img src={staticFile(s.photo)} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '30% center', transform: `scale(${zoom})`}} />
      <AbsoluteFill style={{background: 'linear-gradient(180deg,rgba(0,0,0,.35) 0%,rgba(0,0,0,0) 16%,rgba(0,0,0,0) 45%,rgba(0,0,0,.72) 68%,rgba(0,0,0,.95) 100%)'}} />
      <div style={{position: 'absolute', top: 150, width: '100%', textAlign: 'center', font: '700 28px Montserrat', letterSpacing: '.12em', color: '#F4ECDF', opacity: .85}}>{handle}</div>
      <div style={{position: 'absolute', left: 80, right: 80, bottom: 300, textAlign: 'center', color: '#F4ECDF'}}>
        <div style={{...tr(5), font: '700 30px Montserrat', letterSpacing: '.34em', textTransform: 'uppercase', color: '#E6C9A0', marginBottom: 28}}>{s.label}</div>
        <div style={{...tr(12), fontFamily: 'Oswald', fontWeight: 700, textTransform: 'uppercase', lineHeight: 1, fontSize: 116}}>{s.head}</div>
        <div style={{...tr(22), font: "italic 400 50px/1.3 'PT Serif'", marginTop: 32}}>{s.sub}</div>
        {cta && <div style={{...tr(34), display: 'inline-block', marginTop: 48, padding: '22px 50px', border: '3px solid #F4ECDF', borderRadius: 80, font: '700 36px Montserrat', letterSpacing: '.08em'}}>{cta}</div>}
      </div>
    </AbsoluteFill>
  );
};

export const Reel: React.FC<typeof reelSchemaDefaults> = ({handle, cta, scenes}) => {
  const {durationInFrames} = useVideoConfig();
  const per = Math.floor(durationInFrames / scenes.length);
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <style>{fonts}</style>
      {scenes.map((s, i) => (
        <Sequence key={i} from={i * per} durationInFrames={per}>
          <SceneView s={s} dur={per} handle={handle} cta={i === scenes.length - 1 ? cta : undefined} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
