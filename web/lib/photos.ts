/** Photos used on the site, all under free licences. Credits are shown in the footer. */
export type Photo = { src: string; author: string; license: string; licenseUrl: string; source: string };

export const PHOTOS = {
  portada: { src: "/photos/portada.jpg", author: "King....", license: "CC BY 2.0", licenseUrl: "https://creativecommons.org/licenses/by/2.0/", source: "https://www.flickr.com/photos/21300369@N06/3931770601" },
  scout: { src: "/photos/scout.jpg", author: "footycomimages", license: "CC BY 2.0", licenseUrl: "https://creativecommons.org/licenses/by/2.0/", source: "https://www.flickr.com/photos/188197504@N02/49834167477" },
  pronosticos: { src: "/photos/pronosticos.jpg", author: "jikatu", license: "CC BY-SA 2.0", licenseUrl: "https://creativecommons.org/licenses/by-sa/2.0/", source: "https://www.flickr.com/photos/7221539@N06/4013623722" },
  historial: { src: "/photos/historial.jpg", author: "dejankrsmanovic", license: "CC BY 2.0", licenseUrl: "https://creativecommons.org/licenses/by/2.0/", source: "https://www.flickr.com/photos/155403590@N07/43736101621" },
  en_racha: { src: "/photos/en-racha.jpg", author: "marfis75", license: "CC BY 2.0", licenseUrl: "https://creativecommons.org/licenses/by/2.0/", source: "https://www.flickr.com/photos/45409431@N00/2485479345" },
  no_encontrado: { src: "/photos/no-encontrado.jpg", author: "Autor desconocido", license: "CC0", licenseUrl: "https://creativecommons.org/publicdomain/zero/1.0/", source: "https://www.rawpixel.com/image/5911893/image-public-domain-free-grass" },
  cesped: { src: "/photos/cesped.jpg", author: "skyseeker", license: "CC BY 2.0", licenseUrl: "https://creativecommons.org/licenses/by/2.0/", source: "https://www.flickr.com/photos/40422902@N00/6829724" },
} satisfies Record<string, Photo>;
