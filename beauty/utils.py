# -*- coding: utf8 -*-

from beauty import config
from beauty.config import feature_names

from os import path
from scipy.spatial import distance
from imutils.face_utils import FaceAligner
from PIL import Image, ImageDraw
import numpy as np
import cv2
import dlib
import face_recognition
import os
import time


def create_dir(outdir):
  if not path.exists(outdir):
    os.makedirs(outdir)


def create_pardir(outfile):
  outdir = path.dirname(outfile)
  create_dir(outdir)


def display_image(image):
  pimage = Image.fromarray(image)
  pdraw = ImageDraw.Draw(pimage)
  pimage.show()


def get_star_name(filepath):
  filename = path.basename(filepath)
  star_name = filename.split('.')[0]
  return star_name


def get_star_images(star_image_dir):
  signature = 'utils.get_star_images'
  image_files = []
  image_extensions = ['jfif', 'jpg', 'jpeg', 'png', 'JPG']
  # star_image_dir = config.star_image_dir
  for par_dir, dirnames, filenames in os.walk(star_image_dir):
    if len(filenames) == 0:
      continue
    for filename in filenames:
      is_image = False
      for image_extension in image_extensions:
        if filename.endswith(image_extension):
          is_image = True
          break
      if not is_image:
        print('%s:%s is not image' % (signature, filename))
        continue
      image_file = path.join(par_dir, filename)
      image_files.append(image_file)
  return image_files

################################################################
# server
################################################################


def respond_failure(message):
  response = {
    'data': {},
    'code': 1,
    'message': message,
  }
  return response


def respond_success(result):
  response = {
    'data': result,
    'code': 0,
    'message': '',
  }
  return response


################################################################
# facial features and encoding
################################################################


def get_aligned_face(image, verbose=False):
  signature = 'utils.get_aligned_face'
  start_time = time.time()
  predictor = face_recognition.api.pose_predictor_68_point
  aligner = FaceAligner(predictor, desiredFaceWidth=256)
  if verbose:
    duration = time.time() - start_time
    print('%s:initialize aligner=%.4fs' % (signature, duration))

  start_time = time.time()
  gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
  face_locations = face_recognition.face_locations(image)
  if len(face_locations) == 0:
    return None
  face_location = face_locations[0]
  top, right, bottom, left = face_location
  rect = dlib.rectangle(left=left, top=top, right=right, bottom=bottom)
  if verbose:
    duration = time.time() - start_time
    print('%s:locate face=%.4fs' % (signature, duration))

  start_time = time.time()
  image = aligner.align(image, gray, rect)
  if verbose:
    duration = time.time() - start_time
    print('%s:align face=%.4fs' % (signature, duration))
  return image

def extract_features(image, verbose=False):
  pass

def extract_encoding(image, verbose=False):
  signature = 'utils.extract_encoding'
  image = get_aligned_face(image, verbose=verbose)
  if image is None:
    return None
  # display_image(image)

  start_time = time.time()
  face_encoding = face_recognition.face_encodings(image)[0]
  if verbose:
    duration = time.time() - start_time
    print('%s:encode face=%.4fs' % (signature, duration))
  return face_encoding

def extract_feature(image, save_image=False, verbose=False):
  signature = 'utils.extract_feature'
  start_time = time.time()
  predictor = face_recognition.api.pose_predictor_68_point
  aligner = FaceAligner(predictor, desiredFaceWidth=256)
  if verbose:
    duration = time.time() - start_time
    print('%s:predictor aligner=%.4fs' % (signature, duration))

  # extension = 'png'
  # line_width = 2
  # filename = path.basename(infile)
  # fields = filename.split('.')
  # outfile = path.join(config.star_face_dir, '%s.%s' % (fields[0], extension))
  # if path.isfile(outfile):
  #   return

  # image = face_recognition.load_image_file(infile)
  # print(type(image), image.shape, image.dtype)
  start_time = time.time()
  gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
  face_locations = face_recognition.face_locations(image)
  if len(face_locations) == 0:
    return None
  face_location = face_locations[0]
  top, right, bottom, left = face_location
  rect = dlib.rectangle(left=left, top=top, right=right, bottom=bottom)
  if verbose:
    duration = time.time() - start_time
    print('%s:face location=%.4fs' % (signature, duration))

  start_time = time.time()
  image = aligner.align(image, gray, rect)
  if verbose:
    duration = time.time() - start_time
    print('%s:align image=%.4fs' % (signature, duration))

  start_time = time.time()
  face_locations = face_recognition.face_locations(image)[:1]
  face_landmarks = face_recognition.face_landmarks(image, face_locations=face_locations)

  # TODO
  # face_encoding = face_recognition.face_encodings(image, known_face_locations=face_locations)[0]
  # print('face encoding', face_encoding.shape, face_encoding.dtype)

  face_location, face_landmark = face_locations[0], face_landmarks[0]
  if verbose:
    duration = time.time() - start_time
    print('%s:face landmark=%.4fs' % (signature, duration))

  start_time = time.time()
  # for feature_name in feature_names:
  #   print('#%s=%d' % (feature_name, len(face_landmark[feature_name])))
  top, right, bottom, left = face_location
  # rescale location to include landmark
  half_width = (right - left) / 2.0
  half_height = (bottom - top) / 2.0
  center_x = (right + left) / 2.0
  center_y = (bottom + top) / 2.0
  scale_m = 1.0
  for feature_name in feature_names:
    for point_x, point_y in face_landmark[feature_name]:
      scale_x = abs((point_x - center_x) / half_width)
      scale_y = abs((point_y - center_y) / half_height)
      scale_m = max(scale_m, scale_x, scale_y)
  top = center_y - half_height * scale_m
  right = center_x + half_width * scale_m
  bottom = center_y + half_height * scale_m
  left = center_x - half_width * scale_m
  # face_location = top, right, bottom, left
  width = right - left
  height = bottom - top
  if verbose:
    duration = time.time() - start_time
    print('%s:rescale face location=%.4fs' % (signature, duration))

  start_time = time.time()
  face_feature = {}
  for feature_name in feature_names:
    feature = []
    for point_x, point_y in face_landmark[feature_name]:
      position_x = (point_x - left) / width
      position_y = (point_y - top) / height
      feature.extend([position_x, position_y])
    face_feature[feature_name] = feature
  location_rect = [
    (left, top),
    (right, top),
    (right, bottom),
    (left, bottom),
    (left, top)
  ]
  if verbose:
    duration = time.time() - start_time
    print('%s:extract features=%.4fs' % (signature, duration))

  if save_image:
    line_width = 2
    pimage = Image.fromarray(image)
    pdraw = ImageDraw.Draw(pimage)
    for feature_name in feature_names:
      pdraw.line(face_landmark[feature_name], width=line_width)
    pdraw.line(location_rect, width=line_width)
    pimage.show()
    # create_pardir(outfile)
    # pimage.save(outfile, extension)

  return face_feature

################################################################
# match star
################################################################

def get_feature(face_feature, feature_names):
  feature = []
  for feature_name in feature_names:
    feature.extend(face_feature[feature_name])
  return feature

def search_star(face_feature, star_features, feature_names):
  face_feature = get_feature(face_feature, feature_names)
  best_star, best_dist = None, np.inf
  for star_name, star_feature in star_features.items():
    if star_feature == None:
      # print(star_name)
      continue
    star_feature = get_feature(star_feature, feature_names)
    dist = distance.euclidean(face_feature, star_feature)
    if dist < best_dist:
      best_dist = dist
      best_star = star_name
  # print('%s %.4f' % (best_star, best_dist))
  star_name = best_star.split('.')[0]
  return star_name, best_dist






